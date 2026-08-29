#!/usr/bin/env python3
"""
Harvests real animated GIFs from Wikimedia Commons into gifs/real/.

    pip install pillow
    python3 tools/fetch-gifs.py --scan      # search, write candidates.json
    python3 tools/fetch-gifs.py --fetch     # download + re-encode the keep list
    python3 tools/fetch-gifs.py --sheet     # contact sheets for eyeballing

Commons needs no API key and its files are licensed for redistribution, which
is why it is the source: Giphy and Tenor both need a key and neither licenses
you to ship their content. Everything kept here is public domain or a CC
licence that permits reuse, and every file's author and licence is recorded in
gifs/real/CREDITS.md and shown in the app.

Originals are re-encoded down to the app's size (a Commons GIF is often several
MB) — that's a derivative work, which every licence used here allows, with
attribution preserved.
"""
import argparse, hashlib, io, json, os, re, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "gifs", "real")
CAND = os.path.join(HERE, "candidates.json")
KEEP = os.path.join(HERE, "keep.json")
API = "https://commons.wikimedia.org/w/api.php"
UA = "ImposterGameBuild/1.0 (https://github.com/jtennant/UltimateImposter-; offline party game)"

# Output sizing, matched to the drawn pack.
W, FRAMES_MAX, COLORS = 224, 14, 48
MAX_BYTES = 130_000            # per output file; re-encoded harder if over

# Licences that allow redistribution of a derivative. Anything else is dropped.
OK_LICENCE = re.compile(
    r"^(cc0|cc-zero|cc-by(-sa)?-[0-9.]+|cc-by(-sa)?|pd-|public domain|no restrictions"
    r"|attribution|copyrighted free use|fal)", re.I)

QUERIES = [
    "cat", "dog", "horse gallop", "bird flight", "butterfly", "fish swimming", "jellyfish",
    "snail", "octopus", "bee", "spider", "elephant", "penguin", "dolphin", "snake", "frog",
    "volcano eruption", "lightning", "tornado", "ocean wave", "waterfall", "aurora",
    "solar eclipse", "moon phases", "geyser", "snowflake", "rain", "fire flame", "sunset",
    "pendulum", "steam engine", "piston engine", "gears", "windmill", "wind turbine",
    "clock escapement", "newton's cradle", "dna", "heart beating", "planet orbit",
    "solar system", "satellite orbit", "rocket launch", "helicopter", "propeller",
    "spring oscillation", "magnet field", "wave interference", "pulley", "bicycle",
    "sewing machine", "typewriter", "printing press", "hourglass", "metronome",
    "football", "basketball", "tennis", "boxing", "running", "swimming", "gymnastics",
    "skiing", "cycling", "dancing", "juggling", "skateboard", "somersault",
    "traffic light", "escalator", "ferris wheel", "carousel", "roller coaster", "fountain",
    "fireworks", "balloon", "candle", "coffee", "popcorn", "kettle boiling", "electric fan",
    "dice roll", "playing cards", "chess", "yo-yo", "spinning top", "dominoes",
    "soap bubble", "water splash", "water drop", "smoke", "steam", "explosion",
    "walking cycle", "handshake", "clapping", "waving hand", "jumping", "blinking eye",
    "train", "aeroplane", "sailing boat", "hot air balloon", "car engine", "wheel rolling",
    "umbrella", "flag waving", "kaleidoscope", "pinwheel", "swing", "seesaw", "slinky",
]


def get(params):
    params = dict(params, format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt == 4:
                print("   ! give up:", e)
                return {}
            time.sleep(2 * (attempt + 1))
    return {}


def strip_html(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return re.sub(r"\s+", " ", s).strip()


def clean_artist(s):
    """Commons wraps unattributed uploads in boilerplate; keep just the name."""
    s = strip_html(s)
    m = re.match(r"No machine-readable author provided\.\s*(.+?)\s*assumed\b", s, re.I)
    if m:
        s = m.group(1)
    s = re.sub(r"\(based on copyright claims\)\.?", "", s, flags=re.I)
    s = re.sub(r"^(User:|user )", "", s.strip(), flags=re.I)
    s = re.sub(r"\s+", " ", s).strip(" .,")
    return s or "unknown"


def scan():
    found = {}
    for i, q in enumerate(QUERIES):
        data = get({
            "action": "query", "generator": "search",
            "gsrsearch": f"filemime:image/gif {q}", "gsrnamespace": 6, "gsrlimit": 10,
            "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata",
        })
        pages = data.get("query", {}).get("pages", []) or []
        n = 0
        for p in pages:
            ii = (p.get("imageinfo") or [{}])[0]
            if ii.get("mime") != "image/gif":
                continue
            em = ii.get("extmetadata", {})
            lic = (em.get("License", {}).get("value")
                   or em.get("LicenseShortName", {}).get("value") or "")
            if not OK_LICENCE.match(lic.strip()):
                continue
            if not (160 <= ii.get("width", 0) <= 4000) or ii.get("size", 0) > 12_000_000:
                continue
            title = p["title"]
            found[title] = {
                "title": title, "query": q, "url": ii["url"],
                "w": ii["width"], "h": ii["height"], "bytes": ii["size"],
                "licence": strip_html(em.get("LicenseShortName", {}).get("value") or lic),
                "artist": clean_artist(em.get("Artist", {}).get("value"))[:120],
                "descurl": ii.get("descriptionurl", ""),
            }
            n += 1
        print(f"[{i+1:3d}/{len(QUERIES)}] {q:24s} +{n}  (total {len(found)})")
        time.sleep(0.7)
    with open(CAND, "w") as f:
        json.dump(sorted(found.values(), key=lambda r: r["title"]), f, indent=1)
    print(f"\n{len(found)} candidates -> {CAND}")


def slug(title):
    s = re.sub(r"^File:", "", title)
    s = re.sub(r"\.gif$", "", s, flags=re.I)
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:48]


def tag_from(title):
    s = re.sub(r"^File:", "", title)
    s = re.sub(r"\.gif$", "", s, flags=re.I)
    s = re.sub(r"\b(animation|animated|animate|gif|loop|looped|small|large|final|"
               r"wikipedia|commons|example|demo|v\d+)\b", " ", s, flags=re.I)
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[_\-]+", " ", s)
    s = re.sub(r"\d{3,}", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" -,")
    return s.lower()[:40] or "unknown"


THUMB_PX = 250          # a standard Wikimedia thumbnail width; others are refused


def thumb_of(url):
    """Rewrite an original's URL to its 250px thumbnail.

    Commons throttles bulk downloads of originals hard (HTTP 429) and asks
    you to take thumbnails instead. Theirs stay animated, are a fraction of
    the size, and are already close to the width this app renders at — so
    this is both the polite path and the better one.

        .../commons/a/ab/Name.gif  ->  .../commons/thumb/a/ab/Name.gif/250px-Name.gif
    """
    url = url.split("?")[0]                 # the API tacks a utm_* query onto it
    m = re.match(r"(https://upload\.wikimedia\.org/wikipedia/commons)/(\w)/(\w\w)/([^/]+)$", url)
    if not m:
        return None
    base, a, ab, name = m.groups()
    return f"{base}/thumb/{a}/{ab}/{name}/{THUMB_PX}px-{name}"


def download(url):
    """Thumbnail first, original only if that 404s."""
    thumb = thumb_of(url)
    if thumb:
        try:
            return _get(thumb)
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
    return _get(url)


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5:
                raise
            wait = 20 * (attempt + 1)
            print(f"      429, waiting {wait}s", flush=True)
            time.sleep(wait)
        except Exception:
            if attempt == 5:
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("unreachable")


def reencode(raw, colors=COLORS, width=W):
    """Downscale and thin out an original; returns (bytes, frames) or None."""
    from PIL import Image, ImageSequence
    im = Image.open(io.BytesIO(raw))
    frames = [f.convert("RGBA") for f in ImageSequence.Iterator(im)]
    if len(frames) < 2:
        return None
    durations = []
    for f in ImageSequence.Iterator(Image.open(io.BytesIO(raw))):
        durations.append(f.info.get("duration") or 80)
    step = max(1, -(-len(frames) // FRAMES_MAX))     # ceil: actually caps the count
    keep, keep_ms = [], []
    for i in range(0, len(frames), step):
        keep.append(frames[i])
        keep_ms.append(sum(durations[i:i + step]) or 80)
    flat = []
    for f in keep:
        bg = Image.new("RGBA", f.size, (18, 22, 46, 255))
        bg.alpha_composite(f)
        rgb = bg.convert("RGB")
        w, h = rgb.size
        sc = width / max(w, h)
        rgb = rgb.resize((max(1, round(w * sc)), max(1, round(h * sc))), Image.LANCZOS)
        flat.append(rgb.convert("P", palette=Image.ADAPTIVE, colors=colors, dither=Image.NONE))
    buf = io.BytesIO()
    flat[0].save(buf, format="GIF", save_all=True, append_images=flat[1:],
                 duration=[max(40, min(400, d)) for d in keep_ms], loop=0, optimize=True)
    return buf.getvalue(), len(flat)


def fetch():
    os.makedirs(OUT, exist_ok=True)
    rows = json.load(open(KEEP if os.path.exists(KEEP) else CAND))
    index, credits, seen_tags = [], [], set()
    for i, rec in enumerate(rows):
        tag = rec.get("tag") or tag_from(rec["title"])
        if tag in seen_tags:
            print(f"  skip dup tag {tag}")
            continue
        name = slug(rec["title"]) + ".gif"
        path = os.path.join(OUT, name)
        try:
            if not os.path.exists(path + ".src"):
                raw = download(rec["url"])
                open(path + ".src", "wb").write(raw)
                time.sleep(0.5)
            else:
                raw = open(path + ".src", "rb").read()
            out = reencode(raw)
            if not out:
                print(f"  [{i+1}] not animated: {rec['title']}", flush=True)
                continue
            for colors, width in ((32, 224), (24, 192), (16, 176)):     # keep files small
                if len(out[0]) <= MAX_BYTES:
                    break
                out = reencode(raw, colors, width) or out
            data, nframes = out
            open(path, "wb").write(data)
        except Exception as e:
            print(f"  [{i+1}] failed {rec['title']}: {e}", flush=True)
            continue
        seen_tags.add(tag)
        index.append({"file": name, "tag": tag})
        credits.append({**rec, "file": name, "tag": tag, "frames": nframes,
                        "out_bytes": len(data)})
        print(f"  [{i+1:3d}] {tag:32s} {len(data)//1024:4d} KB  {nframes} frames", flush=True)
    with open(os.path.join(OUT, "index.json"), "w") as f:
        json.dump(index, f, indent=0)
    with open(os.path.join(OUT, "credits.json"), "w") as f:
        json.dump(credits, f, indent=1)
    keep_files = {c["file"] for c in credits}
    for name in sorted(os.listdir(OUT)):                # drop files cut from keep.json
        if name.endswith(".gif") and name not in keep_files:
            os.remove(os.path.join(OUT, name))
            print("  removed", name, flush=True)
    write_credits_md(credits)
    patch_app(os.path.join(HERE, "..", "index.html"), credits)
    total = sum(c["out_bytes"] for c in credits)
    print(f"\n{len(index)} GIFs, {total/1048576:.1f} MB")


def patch_app(html_path, credits):
    """Inline the listing (with attribution) into index.html — same reason as
    the drawn pack: fetch() of a local file is blocked on file://."""
    def js(s):
        return json.dumps(s or "", ensure_ascii=False)
    with open(html_path) as f:
        src = f.read()
    start, end = "/* REAL:start */", "/* REAL:end */"
    i, j = src.index(start), src.index(end)
    body = ",".join(
        "{f:%s,t:%s,a:%s,l:%s,c:%s}" % (
            js(c["file"]), js(c["tag"]), js(c["artist"]), js(c["licence"]),
            js(re.sub(r"^File:", "", c["title"])))
        for c in sorted(credits, key=lambda r: r["tag"]))
    with open(html_path, "w") as f:
        f.write(src[:i] + start + "\nconst REAL = [" + body + "];\n" + src[j:])
    print(f"inlined {len(credits)} real entries into index.html")


def write_credits_md(credits):
    lines = ["# Credits — gifs/real/", "",
             "Animated GIFs harvested from [Wikimedia Commons](https://commons.wikimedia.org)",
             "by `tools/fetch-gifs.py`, and re-encoded smaller for the app. Each is public",
             "domain or under a CC licence that permits reuse; author and licence below.", "",
             "| Tag | File | Author | Licence | Source |", "|---|---|---|---|---|"]
    for c in sorted(credits, key=lambda r: r["tag"]):
        art = (c.get("artist") or "—").replace("|", "/")
        lines.append(f"| {c['tag']} | `{c['file']}` | {art} | {c['licence']} | "
                     f"[Commons]({c['descurl']}) |")
    with open(os.path.join(OUT, "CREDITS.md"), "w") as f:
        f.write("\n".join(lines) + "\n")


def sheet():
    from PIL import Image, ImageDraw, ImageFont, ImageSequence
    idx = json.load(open(os.path.join(OUT, "index.json")))
    TH, COLS, PAD = 150, 6, 18
    font = ImageFont.load_default(11)
    for part in range((len(idx) + 35) // 36):
        rows = idx[part * 36:(part + 1) * 36]
        R = (len(rows) + COLS - 1) // COLS
        sh = Image.new("RGB", (COLS * TH, R * (TH + PAD)), (10, 12, 26))
        d = ImageDraw.Draw(sh)
        for i, rec in enumerate(rows):
            fr = [f.convert("RGB") for f in
                  ImageSequence.Iterator(Image.open(os.path.join(OUT, rec["file"])))]
            im = fr[min(len(fr) // 2, len(fr) - 1)]
            im.thumbnail((TH, TH), Image.LANCZOS)
            x, y = (i % COLS) * TH, (i // COLS) * (TH + PAD)
            sh.paste(im, (x + (TH - im.width) // 2, y + (TH - im.height) // 2))
            d.text((x + 3, y + TH + 3), rec["tag"][:26], fill=(200, 205, 240), font=font)
        p = os.path.join(HERE, f"real-sheet{part}.png")
        sh.save(p)
        print("wrote", p)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--sheet", action="store_true")
    a = ap.parse_args()
    if a.scan: scan()
    if a.fetch: fetch()
    if a.sheet: sheet()
    if not (a.scan or a.fetch or a.sheet): ap.print_help()
