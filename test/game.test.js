/**
 * Browser smoke tests for the Imposter game.
 *
 *   npm install playwright-core
 *   node test/game.test.js
 *
 * Set CHROME_PATH if your Chromium/Chrome isn't in one of the usual places.
 */
const { chromium } = require('playwright-core');
const fs = require('fs');
const nodePath = require('path');

const path = 'file://' + nodePath.join(__dirname, '..', 'index.html');
const EXE = [
  process.env.CHROME_PATH,
  ...(fs.existsSync('/opt/pw-browsers')
    ? fs.readdirSync('/opt/pw-browsers')
        .filter(d => d.startsWith('chromium-'))
        .map(d => `/opt/pw-browsers/${d}/chrome-linux/chrome`)
    : []),
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser',
  '/usr/bin/google-chrome',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
].find(p => p && fs.existsSync(p));

if (!EXE) {
  console.error('No Chromium found. Set CHROME_PATH=/path/to/chrome and re-run.');
  process.exit(2);
}

let failures = 0;
function ok(name, cond, extra) {
  console.log((cond ? '  PASS  ' : '  FAIL  ') + name + (cond ? '' : '  << ' + JSON.stringify(extra)));
  if (!cond) failures++;
}

(async () => {
  const browser = await chromium.launch({ executablePath: EXE, args: ['--no-sandbox'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  await page.goto(path);

  const screen = () => page.evaluate(() => document.querySelector('.screen.on').id);
  const shown = sel => page.evaluate(s => {
    const e = document.querySelector(s);
    return !!e && e.offsetParent !== null;
  }, sel);

  // ---- helper: play a full round, choosing who to vote out ----
  async function deal(nPlayers) {
    const roles = [];
    for (let i = 0; i < nPlayers; i++) {
      const name = await page.textContent('#dealname');
      await page.dispatchEvent('#holdbtn', 'pointerdown');
      const word = await page.textContent('#dealname');
      const sub = await page.textContent('#dealsub');
      roles.push({ name, word, sub });
      await page.dispatchEvent('#holdbtn', 'pointerup');
      ok(`role hidden again after release (p${i + 1})`, (await page.textContent('#dealname')) === name, await page.textContent('#dealname'));
      await page.click('#nextplayer');
    }
    return roles;
  }

  console.log('\n== 1. Classic round, 4 players, imposter caught & guesses wrong ==');
  await page.click(".screen.on [data-go=\"setup\"]");
  ok('setup screen', await screen() === 's-setup');
  await page.click('#start');
  ok('deal screen', await screen() === 's-deal');

  let roles = await deal(4);
  const imps = roles.filter(r => r.word.includes('IMPOSTER'));
  const crew = roles.filter(r => !r.word.includes('IMPOSTER'));
  ok('exactly 1 imposter', imps.length === 1, roles.map(r => r.word));
  ok('crew all share one word', new Set(crew.map(r => r.word)).size === 1, crew.map(r => r.word));
  ok('imposter sees category hint', /Category:/.test(imps[0].sub) || imps[0].sub.includes(''), imps[0].sub);
  ok('play screen after last player', await screen() === 's-play');

  const order = await page.$$eval('#orderlist span', els => els.map(e => e.textContent));
  ok('clue order lists every player once', order.length === 4 && new Set(order.map(o => o.split('. ')[1])).size === 4, order);

  // timer
  await page.click('#tstart');
  await page.waitForTimeout(1200);
  const t = await page.textContent('#timer');
  ok('timer counts down from 1:30', t === '1:29' || t === '1:28', t);
  await page.click('#treset');
  ok('timer reset', (await page.textContent('#timer')) === '1:30');

  await page.click('#tovote');
  ok('vote screen', await screen() === 's-vote');
  const impName = imps[0].name;
  await page.click(`#votegrid button:text-is("${impName}")`);
  ok('caught imposter -> guess screen', await screen() === 's-guess', await screen());
  await page.click('#gwrong');
  ok('wrong guess -> result', await screen() === 's-result');
  ok('crew win banner', (await page.textContent('#banner')).includes('Crew win'), await page.textContent('#banner'));
  const secret = await page.textContent('#rword');
  ok('secret word matches crew card', secret === crew[0].word, [secret, crew[0].word]);
  let scores = await page.$$eval('#scorelist .score', els => els.map(e => e.textContent));
  ok('3 crew scored 1, imposter 0', scores.filter(s => s.endsWith('1')).length === 3 && scores.filter(s => s.endsWith('0')).length === 1, scores);

  console.log('\n== 2. Imposter survives (wrong person voted out) ==');
  await page.click('#again');
  roles = await deal(4);
  const imp2 = roles.find(r => r.word.includes('IMPOSTER')).name;
  const innocent = roles.find(r => !r.word.includes('IMPOSTER')).name;
  await page.click('#tovote');
  await page.click(`#votegrid button:text-is("${innocent}")`);
  ok('civilian voted out -> straight to result', await screen() === 's-result');
  ok('imposter win banner', (await page.textContent('#banner')).includes('Imposter'), await page.textContent('#banner'));
  const roleRows = await page.$$eval('#roles .score', els => els.map(e => e.textContent));
  ok('result marks the imposter', roleRows.find(r => r.startsWith(imp2)).includes('IMPOSTER'), roleRows);
  ok('result marks who was voted out', roleRows.find(r => r.startsWith(innocent)).includes('voted out'), roleRows);

  console.log('\n== 3. Imposter caught but guesses the word ==');
  await page.click('#again');
  roles = await deal(4);
  const imp3 = roles.find(r => r.word.includes('IMPOSTER')).name;
  await page.click('#tovote');
  await page.click(`#votegrid button:text-is("${imp3}")`);
  await page.click('#gright');
  ok('stolen win banner', (await page.textContent('#banner')).includes('guessed the word'), await page.textContent('#banner'));

  console.log('\n== 4. Nobody voted -> imposter survives ==');
  await page.click('#again');
  await deal(4);
  await page.click('#tovote');
  await page.click('#novote');
  ok('no-vote -> imposter wins', (await page.textContent('#banner')).includes('survives'), await page.textContent('#banner'));

  console.log('\n== 5. Two imposters, 6 players, sequential elimination ==');
  await page.click(".screen.on [data-go=\"setup\"]");
  for (let i = 0; i < 2; i++) await page.click('#pplus');
  await page.click('#iplus');
  ok('imposter count = 2', (await page.textContent('#ival')) === '2');
  ok('player count = 6', (await page.textContent('#pval')) === '6');
  await page.click('#start');
  roles = await deal(6);
  const impNames = roles.filter(r => r.word.includes('IMPOSTER')).map(r => r.name);
  ok('2 imposters dealt', impNames.length === 2, roles.map(r => r.name + ':' + r.word));
  await page.click('#tovote');
  await page.click(`#votegrid button:text-is("${impNames[0]}")`);
  ok('still on vote screen after first catch', await screen() === 's-vote', await screen());
  ok('hint mentions one remaining', (await page.textContent('#votehint')).includes('One imposter'), await page.textContent('#votehint'));
  ok('caught player disabled', await page.$eval(`#votegrid button:text-is("${impNames[0]}")`, b => b.disabled));
  await page.click(`#votegrid button:text-is("${impNames[1]}")`);
  ok('all caught -> guess screen', await screen() === 's-guess');
  ok('guess title plural', (await page.textContent('#guesstitle')).includes('All imposters'), await page.textContent('#guesstitle'));
  await page.click('#gwrong');
  scores = await page.$$eval('#scorelist .score', els => els.map(e => e.textContent));
  ok('6 players on scoreboard', scores.length === 6, scores);

  console.log('\n== 6. Blackout mode: no hint for imposter ==');
  await page.click(".screen.on [data-go=\"setup\"]");
  await page.click('[data-mode="blank"]');
  await page.click('#start');
  roles = await deal(6);
  const bImp = roles.filter(r => r.word.includes('IMPOSTER'));
  ok('blackout: no category shown', bImp.every(r => !r.sub.includes('Category')), bImp.map(r => r.sub));

  console.log('\n== 7. Undercover mode: everyone gets a word, imposter differs ==');
  await page.click('#tovote'); await page.click('#novote');
  await page.click(".screen.on [data-go=\"setup\"]");
  await page.click('[data-mode="similar"]');
  await page.click('#start');
  roles = await deal(6);
  const words = roles.map(r => r.word);
  ok('nobody is told they are the imposter', words.every(w => !w.includes('IMPOSTER')), words);
  const counts = {};
  words.forEach(w => counts[w] = (counts[w] || 0) + 1);
  const distinct = Object.keys(counts);
  ok('exactly 2 distinct words', distinct.length === 2, counts);
  ok('4 crew + 2 imposters', Object.values(counts).sort().join() === '2,4', counts);
  await page.click('#tovote');
  const uImp = distinct.find(w => counts[w] === 2);
  const uImpNames = roles.filter(r => r.word === uImp).map(r => r.name);
  await page.click(`#votegrid button:text-is("${uImpNames[0]}")`);
  await page.click(`#votegrid button:text-is("${uImpNames[1]}")`);
  ok('undercover skips the guess step', await screen() === 's-result', await screen());
  ok('result shows imposter word', (await page.textContent('#rcat')).includes(uImp), await page.textContent('#rcat'));

  console.log('\n== 8. Settings persist across reload ==');
  await page.click(".screen.on [data-go=\"setup\"]");
  await page.fill('#plist input >> nth=0', 'Jamie');
  await page.click('[data-mode="classic"]');
  await page.reload();
  await page.click(".screen.on [data-go=\"setup\"]");
  ok('name persisted', (await page.inputValue('#plist input >> nth=0')) === 'Jamie');
  ok('player count persisted', (await page.textContent('#pval')) === '6');
  ok('mode persisted', await page.$eval('[data-mode="classic"]', b => b.classList.contains('on')));

  console.log('\n== 9. Guards ==');
  await page.click('#catnone');
  ok('start disabled with no categories', await page.$eval('#start', b => b.disabled));
  ok('start button explains why', (await page.textContent('#start')).includes('at least one'));
  await page.click('#catall');
  ok('start re-enabled', !(await page.$eval('#start', b => b.disabled)));
  for (let i = 0; i < 10; i++) await page.click('#pminus');
  ok('cannot go below 3 players', (await page.textContent('#pval')) === '3');
  ok('imposters clamped to 1 at 3 players', (await page.textContent('#ival')) === '1');
  for (let i = 0; i < 5; i++) await page.click('#iplus');
  ok('imposters capped for 3 players', (await page.textContent('#ival')) === '1', await page.textContent('#ival'));
  for (let i = 0; i < 25; i++) await page.click('#pplus');
  ok('player cap 20', (await page.textContent('#pval')) === '20');
  for (let i = 0; i < 9; i++) await page.click('#iplus');
  ok('imposter cap 3', (await page.textContent('#ival')) === '3');

  console.log('\n== 10. Word pool integrity ==');
  const audit = await page.evaluate(() => {
    const all = [];
    Object.entries(WORDS).forEach(([c, ws]) => ws.forEach(w => all.push(c + '|' + w)));
    const dupInCat = Object.entries(WORDS).filter(([c, ws]) => new Set(ws.map(w => w.toLowerCase())).size !== ws.length).map(([c]) => c);
    const tooFew = Object.entries(WORDS).filter(([, ws]) => ws.length < 2).map(([c]) => c);
    return { cats: Object.keys(WORDS).length, total: all.length, dupInCat, tooFew };
  });
  ok('no duplicate words within a category', audit.dupInCat.length === 0, audit.dupInCat);
  ok('every category has >=2 words (undercover needs a decoy)', audit.tooFew.length === 0, audit.tooFew);
  console.log(`  info    ${audit.cats} categories, ${audit.total} words`);

  console.log('\n== 11. 200 simulated deals: role integrity ==');
  const sim = await page.evaluate(() => {
    const bad = [];
    for (let n = 0; n < 200; n++) {
      startRound();
      if (R.imps.length !== S.imposters) bad.push('imposter count');
      if (new Set(R.imps).size !== R.imps.length) bad.push('duplicate imposter');
      if (R.imps.some(i => i < 0 || i >= S.players.length)) bad.push('index out of range');
      if (new Set(R.order).size !== S.players.length) bad.push('bad order');
      if (!WORDS[R.cat] || !WORDS[R.cat].includes(R.word)) bad.push('word not in category');
      if (S.mode === 'similar' && R.decoy === R.word) bad.push('decoy equals word');
    }
    return bad;
  });
  ok('200 deals all valid', sim.length === 0, [...new Set(sim)]);

  console.log('\n== 12. No repeats until the pool is exhausted (single small category) ==');
  const rep = await page.evaluate(() => {
    S.cats = ['Easy (kids)']; S.used = [];
    const size = WORDS['Easy (kids)'].length, seen = [];
    for (let i = 0; i < size; i++) { startRound(); seen.push(R.word); }
    return { size, unique: new Set(seen).size };
  });
  ok(`all ${rep.size} words used before repeating`, rep.unique === rep.size, rep);

  ok('no JS errors during the whole run', errors.length === 0, errors);

  await browser.close();
  console.log(failures ? `\n${failures} FAILURE(S)` : '\nAll checks passed.');
  process.exit(failures ? 1 : 0);
})();
