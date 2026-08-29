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

1. **Deal.** The phone names each player in turn. Tap to see your role; it hides itself again after a few seconds (5/8/12/20, or never — your call), with a countdown bar so you can see it coming. Tap **Hide it** to go early. The hide button is locked for the first half-second, so a double-tap can't skip you past your own role.
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

| Mode | Crew get | The imposter gets |
|---|---|---|
| **Classic** | A secret word | "You are the imposter", plus whatever hint level you've set |
| **Undercover** | A word | A *different* word from the same category — and **nobody is told who they are** |
| **GIF** | An animated GIF from your own pack | The GIF's tag, or nothing |

Undercover has no final guess (the imposter had a word all along), so catching them ends it. It's the paranoia mode — you spend the round working out whether the odd one out is you.

### What the imposter gets

A separate setting, so you can dial the difficulty without changing the mode:

- **Nothing** — brutal. Pure improvisation off other people's clues.
- **Category** — "Food & Drink". The standard game.
- **Vague clue** — the shape of the answer only: "2 words · 11 letters". Useless on its own, lethal once a few clues have landed.
- **Shortlist** — four possibilities, one of them right. Generous; good with kids.

### Number of imposters

Anything from **none** to **everyone**, not just the usual one.

- **Zero** is a real round, not a bug. The crew win by voting nobody out, and lose the moment they convict one of their own. Paranoia does the work for you.
- **Everyone** means nobody was given the word. The whole table bluffs at once, one vote ends it, and you all guess the word together at the end — get it and you all win.
- **Secret number** rolls it fresh each round and doesn't tell you: usually one, sometimes none, occasionally two or three, rarely the whole table. With this on, "is there even an imposter?" is a live question every round. The app is careful never to leak the count — the crew card says "someone here might not know this. Or nobody. Or everyone", and the vote screen won't tell you how many are left.

Conventional play, if you want it: 3–5 players → 1, 6–8 → 1–2, 9+ → 2–3. Two imposters changes the game a lot — they can corroborate each other, so give the crew more clue rounds.

## GIF mode

Crew see a GIF and give clues about the picture; the imposter gets its tag (or nothing) and has to bluff a reaction to an image they've never seen.

The GIFs are **yours**. There's no GIF search in the app — that would need a network, an API key and someone else's servers, which is exactly what this app is built to avoid. Instead there's a pack manager: **Add from this phone** picks GIFs out of your camera roll or files, and the paste-a-URL box fetches one and stores the file itself, so it still works offline afterwards (many sites block cross-origin fetches — if one does, save the GIF to your phone and add it as a file).

Each GIF gets a tag, taken from the filename and editable in the manager. That tag is what the imposter is given, and what you're all effectively naming when you argue. Files live in IndexedDB on the device and survive reloads and reboots.

One catch: browsers block IndexedDB for pages opened directly from disk (`file://`). GIF mode therefore needs the app installed from a URL, or served over http — the pack manager says so if it detects this. The word game works fine either way.

---

## Options

- **540 words across 18 categories** — pick any combination. Categories are British-flavoured but not obscure; there's an *Easy (kids)* set.
- **No repeats** until the selected pool is exhausted (GIFs too).
- **Auto-hide** the role card after 5/8/12/20 seconds, or leave it up until tapped.
- **Discussion timer** with a beep and a buzz at zero; screen kept awake while you argue.
- **Random clue order** each round — on/off (off = fixed seating order).
- **Scoreboard** persisted across rounds; winners each take a point.
- Player names are editable and remembered. Settings from older versions migrate automatically.

---

## Why this shape

You asked for something you can just *use*, with no server. A pass-the-phone game is the one variant of this genre that genuinely needs zero networking — the secret only has to be kept from people in the room, and the phone changes hands anyway, so one device is the whole architecture. The alternatives (room codes, everyone on their own phone) all require a backend or WebRTC signalling, plus signal in the room, for no gain at a table where you're already looking at each other.

So: one HTML file, vanilla JS, no build step, no dependencies, no analytics, no fonts to fetch. Add a manifest and a service worker on top and the same file becomes an installable offline app. To add words, edit the `WORDS` object near the top of the `<script>` — it's a plain map of category → array.

The role card is tap-to-reveal rather than hold-to-reveal. Holding looked safer, but a long press is the OS's text-selection gesture and fights it on both iOS and Android, and a brief press meant you could blink and miss your own role. A tap plus a visible auto-hide countdown keeps the card off the screen when it's being passed around, without wrestling the platform for the gesture.

---

## Development

No build. Open `index.html` in a browser. For service-worker work you need `http://`, not `file://`:

```bash
python3 -m http.server 8000    # then http://localhost:8000
```

Bumping `CACHE` in `sw.js` forces installed clients to pick up new assets.

The browser test suite (`test/game.test.js`) serves the app over http and drives real rounds in Chromium — the reveal interaction, all three modes, every hint level, zero/some/all imposters, the secret-number distribution, multi-imposter elimination, every win path, the GIF pack (stored, renamed, deleted, surviving a reload), settings migration, input guards, and 400 simulated deals checked for role integrity. 145 checks:

```bash
npm install playwright-core
node test/game.test.js       # CHROME_PATH=... if Chromium isn't found
```

---

## Where the rules came from

Cross-checked against the common published rule sets for the game and its close relatives (The Chameleon, Spyfall, Undercover / Who's the Spy), which agree on the core loop and differ mainly in whether the imposter gets a hint and how the endgame guess works:

- [How to Play the Imposter Word Game — impostergames.org](https://impostergames.org/how-to)
- [Imposter Game Rules — impostergame.net](https://impostergame.net/imposter-game-rules)
- [Imposter Game Rules — findtheimpostergame.com](https://www.findtheimpostergame.com/rules)
- [The Chameleon — Big Potato Games](https://bigpotato.com/products/the-chameleon)
