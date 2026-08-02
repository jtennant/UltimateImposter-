# Imposter 🕵️

A pass-the-phone social deduction word game. One device, 3–20 players, **no server, no accounts, no internet**.

Everyone gets the same secret word — except the imposter, who's flying blind and has to bluff their way through. Crew are hunting the faker; the imposter is hunting the word.

---

## Get it on your phone

**Option A — install it (recommended).** Host the folder anywhere static (GitHub Pages, Netlify, a USB stick on a laptop), open it in your phone's browser once, then **Add to Home Screen**. A service worker caches everything on that first visit, so from then on it launches full-screen and works in aeroplane mode, in a field, in a pub basement with no signal.

To publish with GitHub Pages: repo **Settings → Pages → Source: deploy from branch**, pick the branch and `/ (root)`. Your URL will be `https://<user>.github.io/<repo>/`.

**Option B — just the file.** `index.html` is completely self-contained: all the CSS, the JavaScript and all 540 words are inside it. Download that one file to your phone and open it. No install, no server, works from `file://`. (You lose the home-screen icon and full-screen chrome, that's all.)

Nothing is ever sent anywhere. Player names and scores live in `localStorage` on the device.

---

## How a round works

1. **Deal.** The phone names each player in turn. You *hold* a button to see your role — it's on screen only while your thumb is down, so a slip of the hand doesn't burn you. Release, pass on.
2. **Clues.** The app picks a random speaking order and shows it. Going round, everyone says **one word** about the secret word.
3. **Discuss.** Optional timer (45s / 90s / 2m / 3m) with a beep and a buzz at zero. The screen is kept awake while you argue.
4. **Vote.** Count votes out loud, tap whoever got the most. With multiple imposters the vote repeats until either a crew member is voted out (imposters win) or all imposters are caught.
5. **Last chance.** If the imposter is caught, they get one guess at the word. Nail it and they steal the win.

**Crew win** by voting out every imposter *and* denying the final guess.
**Imposter wins** by surviving the vote, *or* by guessing the word after being caught.

### Clue etiquette

The game only works if clues are honest-but-oblique. Banned: synonyms, definitions, spelling or rhyming hints, the category name, and inside jokes only some players can decode. The skill is calibration — word is **Pizza**: "Naples" is a good clue, "food" is so safe it screams imposter, "pepperoni" hands the imposter the answer.

---

## Modes

| Mode | The imposter sees | Feels like |
|---|---|---|
| **Classic** | "You are the imposter" + the category | The standard game. Enough of a foothold to bluff. |
| **Blackout** | "You are the imposter". Nothing else. | Brutal. Pure improvisation off other people's clues. |
| **Undercover** | A *different word from the same category* — and **nobody is told who they are** | Paranoia mode. You spend the round working out whether the odd one out is you. |

Undercover has no final guess (the imposter had a word all along), so catching them ends it.

### Number of imposters

Standard play is one. The app allows up to 3, capped at `floor((players − 1) / 2)` so imposters can never reach half the table. Rules of thumb from how the game is usually played: 3–5 players → 1, 6–8 → 1–2, 9+ → 2–3. Two imposters changes the game a lot — they can corroborate each other, so give the crew more clue rounds.

---

## Options

- **540 words across 18 categories** — pick any combination. Categories are British-flavoured but not obscure; there's an *Easy (kids)* set.
- **No repeats** until the selected pool is exhausted.
- **Category hint** for the imposter — on/off.
- **Random clue order** each round — on/off (off = fixed seating order).
- **Scoreboard** persisted across rounds; winners each take a point.
- Player names are editable and remembered.

---

## Why this shape

You asked for something you can just *use*, with no server. A pass-the-phone game is the one variant of this genre that genuinely needs zero networking — the secret only has to be kept from people in the room, and the phone changes hands anyway, so one device is the whole architecture. The alternatives (room codes, everyone on their own phone) all require a backend or WebRTC signalling, plus signal in the room, for no gain at a table where you're already looking at each other.

So: one HTML file, vanilla JS, no build step, no dependencies, no analytics, no fonts to fetch. Add a manifest and a service worker on top and the same file becomes an installable offline app. To add words, edit the `WORDS` object near the top of the `<script>` — it's a plain map of category → array.

---

## Development

No build. Open `index.html` in a browser. For service-worker work you need `http://`, not `file://`:

```bash
python3 -m http.server 8000    # then http://localhost:8000
```

Bumping `CACHE` in `sw.js` forces installed clients to pick up new assets.

The browser test suite (`test/game.test.js`) drives real rounds in Chromium — role dealing, all three modes, multi-imposter elimination, every win path, persistence, input guards, and 200 simulated deals checked for role integrity:

```bash
npm install playwright-core
node test/game.test.js
```

---

## Where the rules came from

Cross-checked against the common published rule sets for the game and its close relatives (The Chameleon, Spyfall, Undercover / Who's the Spy), which agree on the core loop and differ mainly in whether the imposter gets a hint and how the endgame guess works:

- [How to Play the Imposter Word Game — impostergames.org](https://impostergames.org/how-to)
- [Imposter Game Rules — impostergame.net](https://impostergame.net/imposter-game-rules)
- [Imposter Game Rules — findtheimpostergame.com](https://www.findtheimpostergame.com/rules)
- [The Chameleon — Big Potato Games](https://bigpotato.com/products/the-chameleon)
