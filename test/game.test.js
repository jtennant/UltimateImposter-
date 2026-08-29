/**
 * Browser smoke tests for the Imposter game.
 *
 *   npm install playwright-core
 *   node test/game.test.js
 *
 * Serves the app over http (IndexedDB, used by the GIF pack, is blocked on
 * file:// in Chromium). Set CHROME_PATH if Chromium isn't in a usual place.
 */
const { chromium } = require('playwright-core');
const http = require('http');
const fs = require('fs');
const nodePath = require('path');

const ROOT = nodePath.join(__dirname, '..');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.png': 'image/png', '.webmanifest': 'application/manifest+json' };

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

// A real (1x1) GIF, so the pack stores something a browser will render.
const GIF_B64 = 'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';

const server = http.createServer((req, res) => {
  const file = nodePath.join(ROOT, decodeURIComponent(req.url.split('?')[0]) === '/' ? 'index.html' : req.url.split('?')[0]);
  if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'content-type': TYPES[nodePath.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = 'http://127.0.0.1:' + server.address().port + '/';

  const browser = await chromium.launch({ executablePath: EXE, args: ['--no-sandbox'] });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  await page.goto(base);

  const screen = () => page.evaluate(() => document.querySelector('.screen.on').id);
  const round = () => page.evaluate(() => ({ word: R.word, cat: R.cat, imps: R.imps, count: R.imps.length, decoy: R.decoy, mode: R.mode }));
  const toSetup = async () => {
    const s = await screen();
    if (s === 's-setup') return;
    if (s === 's-deal') return page.click('#dealcancel');
    if (s === 's-gifs') return page.click('#gifback');
    return page.click('.screen.on [data-go="setup"]');
  };
  const setPlayers = async n => {
    for (let i = 0; i < 20; i++) await page.click('#pminus');          // down to the floor of 3
    for (let i = 3; i < n; i++) await page.click('#pplus');
  };
  const setImposters = async n => {
    for (let i = 0; i < 21; i++) await page.click('#iminus');          // down to 0
    for (let i = 0; i < n; i++) await page.click('#iplus');
  };

  /** Walk the whole pass-the-phone deal, returning what each player saw. */
  async function deal(nPlayers) {
    const seen = [];
    for (let i = 0; i < nPlayers; i++) {
      const name = await page.textContent('#dealname');
      await page.click('#revealbtn');
      seen.push({
        name,
        word: await page.textContent('#dealname'),
        sub: await page.textContent('#dealsub'),
        hint: (await page.isVisible('#dealhint')) ? (await page.textContent('#dealhint')) : '',
        // computed display, not isVisible: a freshly created blob URL has no
        // bounding box until the first decode, which would flake here
        gif: await page.evaluate(() => getComputedStyle(document.querySelector('#dealimg')).display !== 'none')
      });
      await page.click('#revealbtn');                                   // auto-waits out the anti-double-tap lock
      ok(`role hidden again (p${i + 1})`, (await page.textContent('#dealname')) === name, await page.textContent('#dealname'));
      await page.click('#nextplayer');
    }
    return seen;
  }
  const impsOf = seen => seen.filter(r => r.word.includes('IMPOSTER'));

  console.log('\n== 1. Reveal interaction (the OS text-select + missed-reveal fixes) ==');
  const sel = await page.evaluate(() => {
    const b = document.querySelector('#revealbtn'), c = document.querySelector('#revealcard');
    const cs = e => getComputedStyle(e);
    return {
      btn: cs(b).webkitUserSelect || cs(b).userSelect,
      card: cs(c).webkitUserSelect || cs(c).userSelect,
      touch: cs(b).touchAction
    };
  });
  ok('reveal button is not selectable', sel.btn === 'none', sel);
  ok('reveal card is not selectable', sel.card === 'none', sel);
  ok('touch-action manipulation (no double-tap zoom)', sel.touch === 'manipulation', sel);
  // -webkit-touch-callout is iOS-only; desktop Chromium drops it from the
  // CSSOM entirely, so check the source rather than the parsed sheet.
  const src = fs.readFileSync(nodePath.join(ROOT, 'index.html'), 'utf8');
  ok('long-press callout suppressed globally (iOS)', /\*\s*\{[^}]*-webkit-touch-callout:\s*none/.test(src));
  ok('text inputs stay selectable', /input\s*\{[^}]*user-select:\s*text/.test(src));

  await toSetup();
  await page.click('#start');
  ok('reveal starts hidden', !(await page.isVisible('#countdown')));
  await page.click('#revealbtn');
  ok('tap reveals', (await page.textContent('#dealtag')) === 'Player 1');
  ok('countdown bar visible', await page.isVisible('#countdown'));
  ok('seconds remaining shown', /^[0-9]+$/.test((await page.textContent('#secs')).trim()), await page.textContent('#secs'));
  ok('hide is locked briefly so a stray tap cannot skip it', await page.$eval('#revealbtn', b => b.disabled));
  await page.waitForTimeout(700);
  ok('hide unlocks after the lock window', !(await page.$eval('#revealbtn', b => b.disabled)));
  await page.click('#revealbtn');
  ok('tap hides again', (await page.textContent('#dealsub')).includes('Hidden'));

  // auto-hide fires on its own
  await page.evaluate(() => { S.hold = 1; });
  await page.click('#nextplayer');
  await page.click('#revealbtn');
  await page.waitForTimeout(1500);
  ok('auto-hide fires without a tap', (await page.textContent('#dealsub')).includes('Hidden'), await page.textContent('#dealsub'));
  await page.evaluate(() => { S.hold = 8; });
  await page.click('#dealcancel');
  ok('cancel backs out of a deal in progress', await screen() === 's-setup', await screen());

  console.log('\n== 2. Classic round: caught, guesses wrong ==');
  await toSetup();
  await setPlayers(4); await setImposters(1);
  await page.click('#start');
  let seen = await deal(4);
  let imp = impsOf(seen);
  const crew = seen.filter(r => !r.word.includes('IMPOSTER'));
  ok('exactly 1 imposter', imp.length === 1, seen.map(r => r.word));
  ok('crew share one word', new Set(crew.map(r => r.word)).size === 1, crew.map(r => r.word));
  ok('crew told how many are faking', crew[0].sub.includes('One of you'), crew[0].sub);
  await page.click('#tovote');
  await page.click(`#votegrid button:text-is("${imp[0].name}")`);
  ok('caught -> guess screen', await screen() === 's-guess');
  await page.click('#gwrong');
  ok('crew win', (await page.textContent('#banner')).includes('Crew win'), await page.textContent('#banner'));
  let scores = await page.$$eval('#scorelist .score', e => e.map(x => x.textContent));
  ok('3 crew scored, imposter did not', scores.filter(s => s.endsWith('1')).length === 3, scores);

  console.log('\n== 3. Hint levels ==');
  for (const [level, check] of [
    ['none', (h, r) => h === ''],
    ['category', (h, r) => h === 'Category: ' + r.cat],
    ['vague', (h, r) => new RegExp(`^${r.word.trim().split(/\s+/).length} words? · ${r.word.replace(/[^a-z]/gi, '').length} letters?$`).test(h)],
    ['shortlist', (h, r) => h.startsWith('One of these: ') && h.slice(14).split(' · ').length === 4 && h.includes(r.word)]
  ]) {
    await toSetup();
    await page.click(`[data-hint="${level}"]`);
    await page.click('#start');
    seen = await deal(4);
    const r = await round();
    const h = impsOf(seen)[0].hint;
    ok(`hint "${level}" looks right`, check(h, r), { hint: h, word: r.word, cat: r.cat });
    if (level === 'shortlist') {
      const inCat = await page.evaluate(
        ([cat, list]) => list.every(w => WORDS[cat].includes(w)),
        [r.cat, h.slice(14).split(' · ')]
      );
      ok('shortlist decoys come from the same category', inCat, h);
    }
    await page.click('#tovote'); await page.click('#novote');
  }

  console.log('\n== 4. Zero imposters ==');
  await toSetup();
  await page.click('[data-hint="category"]');
  await setImposters(0);
  ok('stepper reads 0', (await page.textContent('#ival')) === '0');
  ok('setup explains the zero-imposter rule', (await page.textContent('#impwarn')).includes('voting nobody out'), await page.textContent('#impwarn'));
  await page.click('#start');
  seen = await deal(4);
  ok('nobody is told they are an imposter', impsOf(seen).length === 0, seen.map(r => r.word));
  ok('crew wording does not give the zero away', seen[0].sub.includes('Or nobody. Or everyone.'), seen[0].sub);
  ok('everyone shares the word', new Set(seen.map(r => r.word)).size === 1, seen.map(r => r.word));
  let before = await page.evaluate(() => JSON.stringify(S.scores));
  await page.click('#tovote');
  await page.click('#votegrid button >> nth=0');
  ok('convicting an innocent loses the round', (await page.textContent('#banner')).includes('turned on your own'), await page.textContent('#banner'));
  ok('nobody scores that round', (await page.evaluate(() => JSON.stringify(S.scores))) === before, before);

  before = await page.evaluate(() => ({ ...S.scores }));
  await page.click('#again');
  await deal(4);
  await page.click('#tovote');
  await page.click('#novote');
  ok('refusing to convict wins it', (await page.textContent('#banner')).includes('no imposter — and you knew it'), await page.textContent('#banner'));
  ok('all four crew scored', await page.evaluate(b => S.players.every(p => (S.scores[p] || 0) === (b[p] || 0) + 1), before), await page.evaluate(() => S.scores));

  console.log('\n== 5. Everyone an imposter ==');
  await toSetup();
  await setImposters(4);
  ok('stepper reads 4', (await page.textContent('#ival')) === '4');
  ok('imphint says everybody', (await page.textContent('#imphint')).includes('Everybody'), await page.textContent('#imphint'));
  await page.click('#start');
  seen = await deal(4);
  ok('all four are imposters', impsOf(seen).length === 4, seen.map(r => r.word));
  await page.click('#tovote');
  await page.click('#votegrid button >> nth=0');
  ok('one vote ends it', await screen() === 's-guess');
  ok('guess screen explains there was no crew', (await page.textContent('#guesssub')).includes('no crew'), await page.textContent('#guesssub'));
  await page.click('#gwrong');
  ok('wrong guess: nobody wins', (await page.textContent('#banner')).includes('Nobody knew'), await page.textContent('#banner'));
  await page.click('#again');
  await deal(4);
  await page.click('#tovote'); await page.click('#votegrid button >> nth=0'); await page.click('#gright');
  ok('right guess: the whole table wins', (await page.textContent('#banner')).includes('still got it'), await page.textContent('#banner'));

  console.log('\n== 6. Secret number ==');
  await toSetup();
  await setImposters(1);
  await page.click('[data-opt="randomImps"]');
  ok('stepper hidden behind a ?', (await page.textContent('#ival')) === '?');
  ok('stepper disabled', await page.$eval('#iplus', b => b.disabled) && await page.$eval('#iminus', b => b.disabled));
  const dist = await page.evaluate(() => {
    const seenCounts = {};
    for (let i = 0; i < 400; i++) { startRound(); seenCounts[R.imps.length] = (seenCounts[R.imps.length] || 0) + 1; }
    renderSetup(); go('setup');       // startRound() navigates; come back
    return seenCounts;
  });
  const keys = Object.keys(dist).map(Number).sort((a, b) => a - b);
  ok('counts stay within 0..players', keys.every(k => k >= 0 && k <= 4), dist);
  ok('zero comes up sometimes', (dist[0] || 0) > 0, dist);
  ok('one is the most common', Object.entries(dist).sort((a, b) => b[1] - a[1])[0][0] === '1', dist);
  ok('everyone-an-imposter is possible but rare', (dist[4] || 0) > 0 && dist[4] < dist[1], dist);

  await page.click('#start');
  seen = await deal(4);
  ok('crew wording never leaks the secret count', seen.every(r => r.word.includes('IMPOSTER') || r.sub.includes('Or nobody. Or everyone.')), seen.map(r => r.sub));
  const secret = await round();
  await page.click('#tovote');
  if (secret.count > 1) {
    await page.click(`#votegrid button:text-is("${seen[secret.imps[0]].name}")`);
    ok('vote hint does not leak how many are left', !/\d/.test(await page.textContent('#votehint')), await page.textContent('#votehint'));
  }
  if (await screen() === 's-vote') await page.click('#novote');
  await page.evaluate(() => { S.randomImps = false; save(); });

  console.log('\n== 7. GIF mode ==');
  await page.reload();
  await toSetup();
  await page.click('[data-mode="gif"]');
  ok('GIF mode blocks start with an empty pack', await page.$eval('#start', b => b.disabled));
  ok('start button says why', (await page.textContent('#start')).includes('Add some GIFs'), await page.textContent('#start'));
  ok('categories hidden in GIF mode', !(await page.isVisible('#catblock')));

  const added = await page.evaluate(async b64 => {
    const bin = atob(b64), bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    for (const tag of ['dancing cat', 'facepalm', 'mic drop', 'awkward wave', 'slow clap']) {
      await addGif(new Blob([bytes], { type: 'image/gif' }), tag);
    }
    renderSetup();
    return GIFS.length;
  }, GIF_B64);
  ok('5 GIFs stored', added === 5, added);
  ok('start unblocked once the pack has GIFs', !(await page.$eval('#start', b => b.disabled)));
  ok('pack count shown in setup', (await page.textContent('#gifcount')).includes('5 GIFs'), await page.textContent('#gifcount'));

  await setImposters(1);
  await page.click('[data-hint="category"]');
  await page.click('#start');
  seen = await deal(4);
  imp = impsOf(seen);
  const gifCrew = seen.filter(r => !r.word.includes('IMPOSTER'));
  let r = await round();
  ok('crew see the GIF, not a word', gifCrew.every(c => c.gif === true), gifCrew.map(c => c.gif));
  ok('imposter does not see the GIF', imp[0].gif === false);
  ok('imposter gets the tag', imp[0].hint === 'Tag: ' + r.word, [imp[0].hint, r.word]);
  ok('crew wording is about seeing, not knowing', gifCrew[0].sub.includes("hasn't seen this"), gifCrew[0].sub);
  await page.click('#tovote');
  await page.click(`#votegrid button:text-is("${imp[0].name}")`);
  await page.click('#gwrong');
  ok('result shows the GIF', await page.isVisible('#rimg img'));
  ok('result labels it as a GIF', (await page.textContent('#rlabel')).includes('GIF'), await page.textContent('#rlabel'));
  ok('result shows the tag', (await page.textContent('#rword')) === r.word, [await page.textContent('#rword'), r.word]);

  await toSetup();
  await page.click('[data-hint="none"]');
  await page.click('#start');
  seen = await deal(4);
  ok('GIF + no hint: imposter gets nothing', impsOf(seen)[0].hint === '', impsOf(seen)[0].hint);
  await page.click('#tovote'); await page.click('#novote');

  await toSetup();
  await page.click('[data-hint="shortlist"]');
  await page.click('#start');
  seen = await deal(4);
  r = await round();
  const shortlist = impsOf(seen)[0].hint.replace('One of these: ', '').split(' · ');
  ok('GIF shortlist offers 4 tags', shortlist.length === 4, shortlist);
  ok('GIF shortlist contains the real tag', shortlist.includes(r.word), [shortlist, r.word]);
  ok('GIF shortlist decoys are real tags from the pack',
    await page.evaluate(list => list.every(t => GIFS.some(g => g.tag === t)), shortlist), shortlist);
  await page.click('#tovote'); await page.click('#novote');

  console.log('\n== 8. GIF pack manager ==');
  await toSetup();
  await page.click('[data-go="gifs"]');
  ok('manager lists every GIF', (await page.$$('.gifcell')).length === 5);
  ok('stats line shows the count', (await page.textContent('#gifstats')).startsWith('5 GIFs'), await page.textContent('#gifstats'));
  await page.fill('.gifcell input >> nth=0', 'renamed tag');
  await page.click('.gifcell .del >> nth=1');
  await page.waitForTimeout(120);
  ok('deleting removes one', (await page.$$('.gifcell')).length === 4);
  await page.reload();
  const persisted = await page.evaluate(async () => { await loadGifs(); return GIFS.map(g => g.tag); });
  ok('rename survives a reload', persisted.includes('renamed tag'), persisted);
  ok('deletion survives a reload', persisted.length === 4, persisted);

  console.log('\n== 9. Undercover mode ==');
  await toSetup();
  await page.click('[data-mode="similar"]');
  ok('hint picker hidden — the imposter is not told who they are', !(await page.isVisible('#hints')));
  await setImposters(2);
  await page.click('#start');
  seen = await deal(4);
  const words = seen.map(s => s.word);
  ok('nobody is labelled imposter', words.every(w => !w.includes('IMPOSTER')), words);
  const counts = {};
  words.forEach(w => counts[w] = (counts[w] || 0) + 1);
  ok('two words, split 2/2', Object.keys(counts).length === 2 && Object.values(counts).join() === '2,2', counts);
  r = await round();
  await page.click('#tovote');
  const undercover = seen.map((s, i) => i).filter(i => r.imps.includes(i));
  await page.click(`#votegrid button:text-is("${seen[undercover[0]].name}")`);
  await page.click(`#votegrid button:text-is("${seen[undercover[1]].name}")`);
  ok('undercover skips the guess step', await screen() === 's-result', await screen());
  ok('result reveals the decoy word', (await page.textContent('#rcat')).includes(r.decoy), await page.textContent('#rcat'));

  console.log('\n== 10. Guards and persistence ==');
  await toSetup();
  await page.click('[data-mode="classic"]');
  await page.click('#catnone');
  ok('no categories blocks start', await page.$eval('#start', b => b.disabled));
  await page.click('#catall');
  await setPlayers(3);
  ok('player floor is 3', (await page.textContent('#pval')) === '3');
  await setImposters(9);
  ok('imposters cannot exceed players', (await page.textContent('#ival')) === '3', await page.textContent('#ival'));
  await setPlayers(5); await setImposters(5);
  await page.click('#pminus');
  ok('imposters clamp down when a player leaves', (await page.textContent('#ival')) === '4', await page.textContent('#ival'));
  await setPlayers(20); await setImposters(1);
  for (let i = 0; i < 5; i++) await page.click('#pplus');
  ok('player cap is 20', (await page.textContent('#pval')) === '20');
  await page.fill('#plist input >> nth=0', 'Jamie');
  await page.reload();
  await toSetup();
  ok('name persisted', (await page.inputValue('#plist input >> nth=0')) === 'Jamie');
  ok('mode persisted', await page.$eval('[data-mode="classic"]', b => b.classList.contains('on')));

  console.log('\n== 11. Migration from the previous settings format ==');
  const migrated = await page.evaluate(() => {
    localStorage.setItem('imposter.v1', JSON.stringify({ mode: 'blank', opt: { hint: true, timer: true, shuffle: true, score: true } }));
    return null;
  });
  await page.reload();
  const after = await page.evaluate(() => ({ mode: S.mode, hint: S.hint, hasBool: typeof S.opt.hint }));
  ok('old "blank" mode becomes classic + no hint', after.mode === 'classic' && after.hint === 'none', after);
  ok('old boolean hint removed', after.hasBool === 'undefined', after);

  console.log('\n== 12. Word pool and 400 simulated deals ==');
  await page.evaluate(() => { localStorage.clear(); });
  await page.reload();
  const audit = await page.evaluate(() => {
    const dupInCat = Object.entries(WORDS).filter(([, ws]) => new Set(ws.map(w => w.toLowerCase())).size !== ws.length).map(([c]) => c);
    const tooFew = Object.entries(WORDS).filter(([, ws]) => ws.length < 5).map(([c]) => c);
    return { cats: Object.keys(WORDS).length, total: Object.values(WORDS).flat().length, dupInCat, tooFew };
  });
  ok('no duplicates within a category', audit.dupInCat.length === 0, audit.dupInCat);
  ok('every category has enough words for a shortlist', audit.tooFew.length === 0, audit.tooFew);
  console.log(`  info    ${audit.cats} categories, ${audit.total} words`);

  const sim = await page.evaluate(() => {
    const bad = [];
    for (const mode of ['classic', 'similar']) {
      for (const count of [0, 1, 2, 4]) {
        S.mode = mode; S.imposters = count; S.players = ['a', 'b', 'c', 'd'];
        for (let i = 0; i < 50; i++) {
          startRound();
          if (R.imps.length !== count) bad.push(mode + '/' + count + ': imposter count');
          if (new Set(R.imps).size !== R.imps.length) bad.push('duplicate imposter');
          if (R.imps.some(i => i < 0 || i >= S.players.length)) bad.push('index out of range');
          if (new Set(R.order).size !== S.players.length) bad.push('bad clue order');
          if (!WORDS[R.cat] || !WORDS[R.cat].includes(R.word)) bad.push('word not in category');
          if (mode === 'similar' && R.decoy === R.word) bad.push('decoy equals word');
        }
      }
    }
    return [...new Set(bad)];
  });
  ok('400 deals across modes and imposter counts all valid', sim.length === 0, sim);

  const rep = await page.evaluate(() => {
    S.mode = 'classic'; S.cats = ['Easy (kids)']; S.used = [];
    const size = WORDS['Easy (kids)'].length, out = [];
    for (let i = 0; i < size; i++) { startRound(); out.push(R.word); }
    return { size, unique: new Set(out).size };
  });
  ok(`all ${rep.size} words used before any repeat`, rep.unique === rep.size, rep);

  ok('no JS errors during the whole run', errors.length === 0, errors);

  await browser.close();
  server.close();
  console.log(failures ? `\n${failures} FAILURE(S)` : '\nAll checks passed.');
  process.exit(failures ? 1 : 0);
})();
