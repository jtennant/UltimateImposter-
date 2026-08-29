#!/usr/bin/env python3
"""
Generates the built-in GIF pack: 100 looping animations drawn from shapes.

    pip install pillow
    python3 tools/make-gifs.py

Writes gifs/*.gif plus gifs/index.json (the tag list the game reads).

Why generated rather than downloaded: the game has to work offline with no
API key, and shipping a hundred real reaction GIFs would mean shipping a
hundred other people's copyrights. These are drawn from primitives, so the
pack is a couple of megabytes, licence-free, and reproducible. Every scene
is a concrete, nameable thing — that is what makes it clueable.

Colours match the app so the cards don't look pasted in.
"""
import math, os, json
from PIL import Image, ImageDraw

W, SS, FRAMES, COLORS = 224, 3, 12, 32
D = W * SS
MS = 90                                   # frame duration -> ~1.1s loop

BG     = (18, 22, 46)
WHITE  = (242, 244, 255)
PURPLE = (124, 92, 255)
CYAN   = (0, 212, 255)
RED    = (255, 77, 109)
AMBER  = (255, 176, 32)
GREEN  = (34, 197, 94)
PINK   = (255, 122, 198)
SLATE  = (60, 68, 120)
DARK   = (38, 44, 82)
BROWN  = (150, 96, 58)

TAU = math.pi * 2


def S(v): return v * D
def P(x, y): return (S(x), S(y))
def mix(a, b, f):
    f = max(0.0, min(1.0, f))
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))
def fade(col, f): return mix(BG, col, f)


class C:
    """Unit-coordinate (0..1) drawing surface, supersampled then downscaled."""

    def __init__(self, bg=BG):
        self.im = Image.new("RGB", (D, D), bg)
        self.d = ImageDraw.Draw(self.im)

    def circle(self, cx, cy, r, fill=None, outline=None, w=0.012):
        self.d.ellipse([S(cx - r), S(cy - r), S(cx + r), S(cy + r)],
                       fill=fill, outline=outline, width=int(S(w)))

    def ellipse(self, cx, cy, rx, ry, fill=None, outline=None, w=0.012):
        self.d.ellipse([S(cx - rx), S(cy - ry), S(cx + rx), S(cy + ry)],
                       fill=fill, outline=outline, width=int(S(w)))

    def rect(self, x0, y0, x1, y1, fill=None, r=0, outline=None, w=0.012):
        box = [S(x0), S(y0), S(x1), S(y1)]
        if r:
            self.d.rounded_rectangle(box, radius=S(r), fill=fill, outline=outline, width=int(S(w)))
        else:
            self.d.rectangle(box, fill=fill, outline=outline, width=int(S(w)))

    def poly(self, pts, fill=None, outline=None):
        self.d.polygon([P(*p) for p in pts], fill=fill, outline=outline)

    def line(self, pts, fill, w=0.02):
        self.d.line([P(*p) for p in pts], fill=fill, width=max(1, int(S(w))), joint="curve")

    def arc(self, cx, cy, r, a0, a1, fill, w=0.02):
        self.d.arc([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], a0, a1, fill=fill, width=max(1, int(S(w))))

    def pie(self, cx, cy, r, a0, a1, fill):
        self.d.pieslice([S(cx - r), S(cy - r), S(cx + r), S(cy + r)], a0, a1, fill=fill)

    def out(self):
        return self.im.resize((W, W), Image.LANCZOS)


# ------------------------------------------------------------------ shapes
def rot(pts, cx, cy, a):
    s, co = math.sin(a), math.cos(a)
    return [(cx + (x - cx) * co - (y - cy) * s, cy + (x - cx) * s + (y - cy) * co) for x, y in pts]

def star_pts(cx, cy, r, n=5, inner=0.42, a0=0.0):
    out = []
    for i in range(n * 2):
        a = a0 - math.pi / 2 + i * math.pi / n
        rr = r if i % 2 == 0 else r * inner
        out.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return out

def heart(c, cx, cy, r, col):
    c.circle(cx - r * 0.52, cy - r * 0.22, r * 0.55, fill=col)
    c.circle(cx + r * 0.52, cy - r * 0.22, r * 0.55, fill=col)
    c.poly([(cx - r * 1.05, cy - r * 0.16), (cx + r * 1.05, cy - r * 0.16), (cx, cy + r * 1.05)], fill=col)

def cloud(c, cx, cy, r, col=SLATE):
    c.ellipse(cx, cy, r * 1.35, r * 0.78, fill=col)
    c.circle(cx - r * 0.55, cy - r * 0.2, r * 0.62, fill=col)
    c.circle(cx + r * 0.5, cy - r * 0.32, r * 0.72, fill=col)

def drop(c, x, y, r, col):
    c.circle(x, y, r, fill=col)
    c.poly([(x - r, y - r * 0.2), (x + r, y - r * 0.2), (x, y - r * 2.4)], fill=col)

def bolt(c, x, y, s, col=AMBER):
    c.poly([(x + .10 * s, y - .5 * s), (x - .16 * s, y + .06 * s), (x + .01 * s, y + .06 * s),
            (x - .09 * s, y + .5 * s), (x + .18 * s, y - .08 * s), (x, y - .08 * s)], fill=col)

def ground(c, y=0.9, col=SLATE):
    c.rect(0, y, 1, 1, fill=col)

def sparkle(c, x, y, r, col, a=0.0):
    c.poly(star_pts(x, y, r, 4, 0.28, a), fill=col)


SCENES = []
def scene(tag):
    def wrap(fn):
        SCENES.append((tag, fn))
        return fn
    return wrap


# ================================================================== SPACE
@scene("rocket launch")
def _(c, t):
    y = 0.80 - 0.52 * t
    ground(c)
    for i in range(7):
        f = (t * 3 + i * 0.14) % 1
        c.circle(0.5 + math.sin(i * 2.1) * 0.035 * f, y + 0.17 + f * 0.2,
                 0.022 + f * 0.045, fill=fade(AMBER if i % 2 else RED, 1 - f * 0.7))
    c.poly([(0.5, y - 0.17), (0.575, y + 0.02), (0.575, y + 0.14), (0.425, y + 0.14), (0.425, y + 0.02)], fill=WHITE)
    c.poly([(0.425, y + 0.05), (0.34, y + 0.18), (0.425, y + 0.15)], fill=RED)
    c.poly([(0.575, y + 0.05), (0.66, y + 0.18), (0.575, y + 0.15)], fill=RED)
    c.circle(0.5, y - 0.03, 0.037, fill=CYAN)

@scene("shooting star")
def _(c, t):
    for i, (sx, sy, r) in enumerate([(0.18, 0.2, 0.012), (0.8, 0.16, 0.009),
                                     (0.66, 0.74, 0.011), (0.26, 0.8, 0.008), (0.9, 0.5, 0.01)]):
        c.circle(sx, sy, r, fill=fade(WHITE, 0.5 + 0.5 * math.sin(t * TAU + i)))
    x = 0.05 + t * 0.9
    y = 0.22 + t * 0.42
    for k in range(9):
        f = k / 9
        c.circle(x - f * 0.2, y - f * 0.095, 0.024 * (1 - f), fill=fade(CYAN, 1 - f))
    c.poly(star_pts(x, y, 0.06, 4, 0.3), fill=WHITE)

@scene("planet orbit")
def _(c, t):
    c.circle(0.5, 0.5, 0.3, outline=DARK, w=0.008)
    c.circle(0.5, 0.5, 0.13, fill=AMBER)
    a = t * TAU
    c.circle(0.5 + 0.3 * math.cos(a), 0.5 + 0.3 * math.sin(a), 0.055, fill=CYAN)

@scene("moon phases")
def _(c, t):
    R = 0.26
    illum = (1 - math.cos(t * TAU)) / 2          # 0 = new, 1 = full
    c.circle(0.5, 0.5, R, fill=DARK)
    c.pie(0.5, 0.5, R, -90, 90, WHITE) if t < 0.5 else c.pie(0.5, 0.5, R, 90, 270, WHITE)
    c.ellipse(0.5, 0.5, R * abs(1 - 2 * illum), R, fill=WHITE if illum > 0.5 else DARK)

@scene("ufo")
def _(c, t):
    y = 0.42 + math.sin(t * TAU) * 0.035
    c.poly([(0.5, y + 0.1), (0.22, 0.99), (0.78, 0.99)], fill=fade(GREEN, 0.13))
    c.circle(0.5, y - 0.03, 0.12, fill=CYAN)
    c.ellipse(0.5, y + 0.04, 0.27, 0.085, fill=WHITE)
    for i in range(5):
        c.circle(0.28 + i * 0.11, y + 0.06, 0.021, fill=AMBER if (int(t * 6) + i) % 2 else RED)

@scene("satellite")
def _(c, t):
    a = math.sin(t * TAU) * 0.25
    c.circle(0.5, 0.5, 0.09, fill=WHITE)
    for sgn in (-1, 1):
        pts = rot([(0.5 + sgn * 0.13, 0.44), (0.5 + sgn * 0.4, 0.44), (0.5 + sgn * 0.4, 0.56), (0.5 + sgn * 0.13, 0.56)], 0.5, 0.5, a)
        c.poly(pts, fill=CYAN)
    for k in range(3):
        f = (t * 2 + k * 0.33) % 1
        c.arc(0.5, 0.5, 0.16 + f * 0.22, -125, -55, fade(AMBER, 1 - f), w=0.014)

@scene("eclipse")
def _(c, t):
    c.circle(0.5, 0.5, 0.24, fill=AMBER)
    for k in range(16):
        a = k * TAU / 16
        c.line([(0.5 + 0.27 * math.cos(a), 0.5 + 0.27 * math.sin(a)),
                (0.5 + 0.34 * math.cos(a), 0.5 + 0.34 * math.sin(a))], fill=fade(AMBER, 0.7), w=0.012)
    c.circle(0.5 - 0.45 + t * 0.9, 0.5, 0.24, fill=BG)

@scene("comet")
def _(c, t):
    x = 0.88 - t * 0.8
    y = 0.3 + t * 0.3
    for k in range(12):
        f = k / 12
        c.circle(x + f * 0.32, y - f * 0.12, 0.05 * (1 - f * 0.8), fill=fade(CYAN, (1 - f) * 0.9))
    c.circle(x, y, 0.06, fill=WHITE)

@scene("starry night")
def _(c, t):
    pts = [(0.14, 0.2), (0.32, 0.44), (0.5, 0.16), (0.7, 0.36), (0.86, 0.22),
           (0.22, 0.68), (0.44, 0.8), (0.62, 0.62), (0.8, 0.76), (0.5, 0.52)]
    for i, (x, y) in enumerate(pts):
        f = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * TAU + i * 1.3))
        sparkle(c, x, y, 0.04 * (0.6 + 0.4 * f), fade(WHITE, f))

@scene("sunrise")
def _(c, t):
    y = 0.78 - t * 0.22
    for k in range(12):
        a = k * TAU / 12 + t * 0.5
        c.line([(0.5 + 0.19 * math.cos(a), y + 0.19 * math.sin(a)),
                (0.5 + 0.3 * math.cos(a), y + 0.3 * math.sin(a))], fill=fade(AMBER, 0.8), w=0.016)
    c.circle(0.5, y, 0.16, fill=AMBER)
    c.rect(0, 0.78, 1, 1, fill=DARK)

# ================================================================ WEATHER
@scene("rain")
def _(c, t):
    cloud(c, 0.5, 0.3, 0.2)
    for i in range(11):
        x = 0.2 + (i * 0.062)
        f = (t + i * 0.09) % 1
        y = 0.46 + f * 0.44
        c.line([(x, y), (x - 0.018, y + 0.08)], fill=CYAN, w=0.014)

@scene("lightning")
def _(c, t):
    flash = t < 0.18 or 0.3 < t < 0.4
    cloud(c, 0.5, 0.3, 0.21, mix(SLATE, WHITE, 0.35 if flash else 0))
    if flash:
        bolt(c, 0.5, 0.66, 0.62, WHITE if t < 0.18 else AMBER)
    else:
        bolt(c, 0.5, 0.66, 0.62, fade(AMBER, 0.22))

@scene("snowfall")
def _(c, t):
    for i in range(14):
        f = (t + i * 0.071) % 1
        x = 0.08 + (i * 0.065) + math.sin(f * TAU + i) * 0.03
        y = 0.02 + f * 0.96
        r = 0.014 + (i % 3) * 0.006
        c.circle(x, y, r, fill=WHITE)
    c.rect(0, 0.93, 1, 1, fill=WHITE)

@scene("rainbow")
def _(c, t):
    for i, col in enumerate([RED, AMBER, GREEN, CYAN, PURPLE]):
        r = 0.44 - i * 0.06
        c.arc(0.5, 0.86, r, 180, 360, fade(col, 0.65 + 0.35 * math.sin(t * TAU + i * 0.6)), w=0.055)
    cloud(c, 0.14, 0.84, 0.12)
    cloud(c, 0.87, 0.84, 0.12)

@scene("tornado")
def _(c, t):
    for i in range(11):
        f = i / 10
        w = 0.06 + f * 0.28
        y = 0.86 - f * 0.66
        x = 0.5 + math.sin(t * TAU + f * 5) * 0.05 * f
        c.ellipse(x, y, w, 0.038, fill=fade(SLATE, 0.45 + 0.55 * f))
    cloud(c, 0.5, 0.16, 0.2)

@scene("heatwave")
def _(c, t):
    c.circle(0.5, 0.44, 0.2 + 0.012 * math.sin(t * TAU), fill=AMBER)
    for k in range(12):
        a = k * TAU / 12 + t * 0.4
        c.line([(0.5 + 0.24 * math.cos(a), 0.44 + 0.24 * math.sin(a)),
                (0.5 + 0.35 * math.cos(a), 0.44 + 0.35 * math.sin(a))], fill=RED, w=0.018)
    for i in range(3):
        y = 0.82 + i * 0.05
        pts = [(x / 20, y + math.sin(x / 20 * 12 + t * TAU + i) * 0.016) for x in range(3, 18)]
        c.line(pts, fill=fade(AMBER, 0.6), w=0.012)

@scene("puddle ripple")
def _(c, t):
    c.ellipse(0.5, 0.62, 0.4, 0.19, fill=DARK)
    for k in range(3):
        f = (t + k / 3) % 1
        c.ellipse(0.5, 0.62, 0.05 + f * 0.33, 0.024 + f * 0.155, outline=fade(CYAN, 1 - f), w=0.012)
    f = (t * 1) % 1
    if f < 0.5:
        drop(c, 0.5, 0.06 + f * 0.9, 0.028, CYAN)

@scene("ocean wave")
def _(c, t):
    for i, (col, off, amp) in enumerate([(DARK, 0.0, 0.05), (SLATE, 0.35, 0.06), (CYAN, 0.7, 0.045)]):
        base = 0.44 + i * 0.13
        pts = [(x / 24, base + math.sin(x / 24 * 7 + t * TAU + off * 6) * amp) for x in range(25)]
        c.poly(pts + [(1, 1), (0, 1)], fill=col)

@scene("cloudy")
def _(c, t):
    cloud(c, 0.34 + math.sin(t * TAU) * 0.04, 0.4, 0.17, SLATE)
    cloud(c, 0.66 - math.sin(t * TAU) * 0.04, 0.58, 0.2, mix(SLATE, WHITE, 0.25))

# ============================================================= FIRE / LIGHT
def flame(c, x, y, s, t, col=AMBER):
    w = 1 + 0.12 * math.sin(t * TAU * 2)
    c.poly([(x, y - s * 1.5 * w), (x + s * 0.55, y - s * 0.3), (x + s * 0.42, y + s * 0.4),
            (x - s * 0.42, y + s * 0.4), (x - s * 0.55, y - s * 0.3)], fill=col)
    c.poly([(x, y - s * 0.85 * w), (x + s * 0.3, y - s * 0.05), (x, y + s * 0.35),
            (x - s * 0.3, y - s * 0.05)], fill=AMBER if col is RED else WHITE)

@scene("campfire")
def _(c, t):
    for a, col in [(-0.5, BROWN), (0.5, BROWN), (0.0, mix(BROWN, DARK, 0.4))]:
        c.poly(rot([(0.28, 0.82), (0.72, 0.82), (0.72, 0.87), (0.28, 0.87)], 0.5, 0.845, a), fill=col)
    flame(c, 0.5, 0.62, 0.16, t, RED)
    for i in range(4):
        f = (t * 2 + i * 0.25) % 1
        c.circle(0.5 + math.sin(f * 5 + i) * 0.09, 0.5 - f * 0.32, 0.012, fill=fade(AMBER, 1 - f))

@scene("candle")
def _(c, t):
    c.rect(0.42, 0.5, 0.58, 0.86, fill=WHITE, r=0.02)
    c.line([(0.5, 0.5), (0.5, 0.45)], fill=DARK, w=0.014)
    flame(c, 0.5, 0.37, 0.09, t)

@scene("fireworks")
def _(c, t):
    for bx, by, col, ph in [(0.33, 0.36, PINK, 0.0), (0.7, 0.3, AMBER, 0.4), (0.52, 0.66, CYAN, 0.72)]:
        f = (t + ph) % 1
        if f < 0.2:
            c.line([(bx, 1.0), (bx, 1.0 - (1.0 - by) * (f / 0.2))], fill=fade(col, 0.9), w=0.014)
            continue
        g = (f - 0.2) / 0.8
        for i in range(14):
            a = i * TAU / 14
            r = 0.03 + g * 0.26
            drop_y = g * g * 0.07
            x, y = bx + r * math.cos(a), by + r * math.sin(a) + drop_y
            c.line([(bx + r * 0.5 * math.cos(a), by + r * 0.5 * math.sin(a) + drop_y), (x, y)],
                   fill=fade(col, 1 - g * 0.8), w=0.026)
            c.circle(x, y, 0.028 * (1 - g * 0.6), fill=fade(WHITE if g < 0.3 else col, 1 - g * 0.7))

@scene("light bulb")
def _(c, t):
    on = math.sin(t * TAU) > -0.2
    col = AMBER if on else DARK
    if on:
        for k in range(10):
            a = k * TAU / 10
            c.line([(0.5 + 0.24 * math.cos(a), 0.42 + 0.24 * math.sin(a)),
                    (0.5 + 0.33 * math.cos(a), 0.42 + 0.33 * math.sin(a))], fill=fade(AMBER, 0.75), w=0.016)
    c.circle(0.5, 0.42, 0.18, fill=col)
    c.rect(0.43, 0.58, 0.57, 0.68, fill=SLATE)
    c.rect(0.45, 0.68, 0.55, 0.76, fill=SLATE, r=0.02)

@scene("lighthouse")
def _(c, t):
    a = t * TAU
    for k in range(2):
        aa = a + k * math.pi
        c.poly([(0.5, 0.36), (0.5 + math.cos(aa - 0.2) * 1.1, 0.36 + math.sin(aa - 0.2) * 1.1),
                (0.5 + math.cos(aa + 0.2) * 1.1, 0.36 + math.sin(aa + 0.2) * 1.1)], fill=fade(AMBER, 0.28))
    c.poly([(0.42, 0.44), (0.58, 0.44), (0.63, 0.92), (0.37, 0.92)], fill=WHITE)
    c.poly([(0.44, 0.62), (0.56, 0.62), (0.585, 0.78), (0.415, 0.78)], fill=RED)
    c.rect(0.41, 0.3, 0.59, 0.44, fill=SLATE, r=0.02)
    c.circle(0.5, 0.36, 0.05, fill=AMBER)
    ground(c, 0.92)

@scene("explosion")
def _(c, t):
    g = t
    for i in range(14):
        a = i * TAU / 14
        r = g * 0.42
        c.circle(0.5 + r * math.cos(a), 0.5 + r * math.sin(a), 0.06 * (1 - g), fill=fade(AMBER, 1 - g))
    c.circle(0.5, 0.5, max(0.001, 0.26 * (1 - g)), fill=fade(WHITE, 1 - g * 0.5))
    c.poly(star_pts(0.5, 0.5, 0.16 + g * 0.2, 8, 0.5, g), fill=fade(RED, 1 - g))

@scene("sparkler")
def _(c, t):
    c.line([(0.32, 0.86), (0.52, 0.52)], fill=SLATE, w=0.022)
    for i in range(18):
        a = (i * 2.39 + t * 3) % TAU
        r = 0.05 + ((i * 0.137 + t) % 1) * 0.26
        x, y = 0.54 + r * math.cos(a), 0.48 + r * math.sin(a)
        c.circle(x, y, 0.012, fill=fade(AMBER if i % 3 else WHITE, 1 - r * 2))
    c.circle(0.54, 0.48, 0.035, fill=WHITE)

@scene("volcano")
def _(c, t):
    for i in range(9):
        f = (t + i * 0.11) % 1
        a = -math.pi / 2 + (i - 4) * 0.16
        x = 0.5 + math.cos(a) * f * 0.42
        y = 0.42 + math.sin(a) * f * 0.42 + f * f * 0.35
        c.circle(x, y, 0.028 * (1 - f * 0.4), fill=fade(RED if i % 2 else AMBER, 1 - f * 0.6))
    c.poly([(0.5, 0.3), (0.95, 0.92), (0.05, 0.92)], fill=SLATE)
    c.poly([(0.5, 0.36), (0.62, 0.62), (0.38, 0.62)], fill=RED)
    ground(c, 0.92)

# =================================================================== TIME
@scene("hourglass")
def _(c, t):
    c.rect(0.28, 0.12, 0.72, 0.18, fill=WHITE, r=0.02)
    c.rect(0.28, 0.82, 0.72, 0.88, fill=WHITE, r=0.02)
    c.poly([(0.33, 0.18), (0.67, 0.18), (0.5, 0.5)], fill=DARK)
    c.poly([(0.33, 0.82), (0.67, 0.82), (0.5, 0.5)], fill=DARK)
    k = 1 - t
    c.poly([(0.5 - 0.17 * k, 0.18 + 0.32 * (1 - k)), (0.5 + 0.17 * k, 0.18 + 0.32 * (1 - k)), (0.5, 0.5)], fill=AMBER)
    c.poly([(0.5 - 0.17 * (1 - k), 0.82), (0.5 + 0.17 * (1 - k), 0.82), (0.5, 0.82 - 0.32 * (1 - k))], fill=AMBER)
    c.line([(0.5, 0.5), (0.5, 0.78)], fill=AMBER, w=0.012)

@scene("alarm clock")
def _(c, t):
    sh = math.sin(t * TAU * 4) * 0.012
    c.circle(0.34 + sh, 0.22, 0.09, fill=SLATE)
    c.circle(0.66 + sh, 0.22, 0.09, fill=SLATE)
    c.circle(0.5 + sh, 0.55, 0.31, fill=WHITE)
    c.circle(0.5 + sh, 0.55, 0.26, fill=DARK)
    a = t * TAU
    c.line([(0.5 + sh, 0.55), (0.5 + sh + 0.14 * math.cos(a - 1.57), 0.55 + 0.14 * math.sin(a - 1.57))], fill=WHITE, w=0.018)
    c.line([(0.5 + sh, 0.55), (0.5 + sh + 0.19 * math.cos(a * 6 - 1.57), 0.55 + 0.19 * math.sin(a * 6 - 1.57))], fill=RED, w=0.012)
    c.circle(0.5 + sh, 0.55, 0.022, fill=RED)

@scene("stopwatch")
def _(c, t):
    c.rect(0.44, 0.06, 0.56, 0.16, fill=SLATE, r=0.02)
    c.circle(0.5, 0.56, 0.33, fill=WHITE)
    c.circle(0.5, 0.56, 0.28, fill=BG)
    for k in range(12):
        a = k * TAU / 12
        c.line([(0.5 + 0.23 * math.cos(a), 0.56 + 0.23 * math.sin(a)),
                (0.5 + 0.26 * math.cos(a), 0.56 + 0.26 * math.sin(a))], fill=SLATE, w=0.01)
    a = t * TAU - 1.57
    c.line([(0.5, 0.56), (0.5 + 0.22 * math.cos(a), 0.56 + 0.22 * math.sin(a))], fill=RED, w=0.016)
    c.circle(0.5, 0.56, 0.025, fill=RED)

@scene("pendulum")
def _(c, t):
    a = math.sin(t * TAU) * 0.7
    c.circle(0.5, 0.16, 0.025, fill=SLATE)
    x, y = 0.5 + 0.52 * math.sin(a), 0.16 + 0.52 * math.cos(a)
    c.line([(0.5, 0.16), (x, y)], fill=SLATE, w=0.014)
    c.circle(x, y, 0.09, fill=CYAN)

@scene("metronome")
def _(c, t):
    a = math.sin(t * TAU) * 0.42
    c.poly([(0.5, 0.1), (0.82, 0.9), (0.18, 0.9)], fill=SLATE)
    x, y = 0.5 + 0.36 * math.sin(a), 0.86 - 0.36 * math.cos(a)
    c.line([(0.5, 0.86), (x, y)], fill=WHITE, w=0.018)
    c.rect(x - 0.05, y - 0.03, x + 0.05, y + 0.03, fill=AMBER, r=0.012)

@scene("sunset")
def _(c, t):
    c.rect(0, 0, 1, 1, fill=mix((30, 24, 60), (90, 40, 70), 0.5 + 0.5 * math.sin(t * TAU)))
    y = 0.5 + t * 0.28
    c.circle(0.5, y, 0.18, fill=mix(AMBER, RED, t))
    c.rect(0, 0.78, 1, 1, fill=(24, 20, 44))
    for k in range(4):
        c.ellipse(0.5, 0.82 + k * 0.05, 0.4 - k * 0.05, 0.012, fill=fade(AMBER, 0.4 - k * 0.08))

# ==================================================================== TECH
@scene("wifi signal")
def _(c, t):
    lit = int(t * 4) % 4
    c.circle(0.5, 0.74, 0.045, fill=CYAN if lit >= 0 else DARK)
    for i in range(3):
        r = 0.16 + i * 0.15
        c.arc(0.5, 0.74, r, 205, 335, CYAN if lit > i else DARK, w=0.045)

@scene("loading spinner")
def _(c, t):
    for i in range(12):
        a = i * TAU / 12
        f = ((i / 12) + t) % 1
        c.circle(0.5 + 0.25 * math.cos(a), 0.5 + 0.25 * math.sin(a), 0.038, fill=mix(DARK, CYAN, f))

@scene("battery charging")
def _(c, t):
    c.rect(0.14, 0.36, 0.8, 0.64, fill=None, outline=WHITE, w=0.028, r=0.05)
    c.rect(0.82, 0.45, 0.9, 0.55, fill=WHITE, r=0.02)
    lvl = 0.18 + 0.6 * t
    c.rect(0.18, 0.4, 0.18 + lvl, 0.6, fill=GREEN, r=0.03)
    bolt(c, 0.47, 0.5, 0.3, WHITE)

@scene("download")
def _(c, t):
    y = 0.12 + t * 0.42
    c.line([(0.5, y - 0.14), (0.5, y + 0.06)], fill=CYAN, w=0.05)
    c.poly([(0.5, y + 0.2), (0.62, y + 0.02), (0.38, y + 0.02)], fill=CYAN)
    c.line([(0.24, 0.8), (0.76, 0.8)], fill=WHITE, w=0.035)
    c.line([(0.24, 0.8), (0.24, 0.7)], fill=WHITE, w=0.035)
    c.line([(0.76, 0.8), (0.76, 0.7)], fill=WHITE, w=0.035)

@scene("progress bar")
def _(c, t):
    c.rect(0.1, 0.44, 0.9, 0.56, fill=DARK, r=0.06)
    c.rect(0.1, 0.44, 0.1 + 0.8 * t, 0.56, fill=GREEN, r=0.06)
    for i in range(3):
        c.circle(0.42 + i * 0.08, 0.68, 0.018, fill=fade(WHITE, 0.3 + 0.7 * ((t * 3 + i * 0.33) % 1)))

@scene("radar")
def _(c, t):
    c.circle(0.5, 0.5, 0.38, fill=(14, 34, 30))
    for r in (0.13, 0.26, 0.38):
        c.circle(0.5, 0.5, r, outline=GREEN, w=0.008)
    a = t * TAU
    for k in range(26):
        aa = a - k * 0.035
        c.line([(0.5, 0.5), (0.5 + 0.38 * math.cos(aa), 0.5 + 0.38 * math.sin(aa))],
               fill=fade(GREEN, 0.9 - k * 0.034), w=0.02)
    blip = (t + 0.3) % 1
    c.circle(0.63, 0.36, 0.028, fill=fade(GREEN, 1 - blip))

@scene("padlock")
def _(c, t):
    shut = t > 0.5
    lift = 0.0 if shut else 0.06
    c.arc(0.5, 0.42 - lift, 0.15, 180, 360, WHITE, w=0.045)
    c.line([(0.35, 0.42 - lift), (0.35, 0.52)], fill=WHITE, w=0.045)
    c.line([(0.65, 0.42 - lift), (0.65, 0.52)], fill=WHITE, w=0.045)
    c.rect(0.28, 0.5, 0.72, 0.86, fill=AMBER if shut else SLATE, r=0.06)
    c.circle(0.5, 0.66, 0.05, fill=DARK)
    c.rect(0.475, 0.66, 0.525, 0.76, fill=DARK)

@scene("new mail")
def _(c, t):
    y = 0.55 + math.sin(t * TAU) * 0.03
    c.rect(0.16, y - 0.2, 0.84, y + 0.2, fill=WHITE, r=0.04)
    c.poly([(0.16, y - 0.2), (0.84, y - 0.2), (0.5, y + 0.04)], fill=SLATE)
    c.circle(0.8, y - 0.22, 0.09, fill=RED)
    sparkle(c, 0.22, y - 0.3, 0.035, fade(AMBER, 0.4 + 0.6 * math.sin(t * TAU * 2)))

@scene("phone ringing")
def _(c, t):
    a = math.sin(t * TAU * 3) * 0.18
    pts = rot([(0.36, 0.24), (0.64, 0.24), (0.64, 0.86), (0.36, 0.86)], 0.5, 0.55, a)
    c.poly(pts, fill=WHITE)
    c.poly(rot([(0.4, 0.3), (0.6, 0.3), (0.6, 0.76), (0.4, 0.76)], 0.5, 0.55, a), fill=CYAN)
    for k in range(3):
        f = (t * 2 + k * 0.33) % 1
        for sgn in (-1, 1):
            c.arc(0.5 + sgn * 0.18, 0.5, 0.1 + f * 0.22, 200 if sgn > 0 else 20, 340 if sgn > 0 else 160,
                  fade(AMBER, 1 - f), w=0.016)

@scene("camera flash")
def _(c, t):
    f = 1 if t < 0.12 else 0
    c.rect(0.12, 0.36, 0.88, 0.82, fill=SLATE, r=0.06)
    c.rect(0.36, 0.28, 0.64, 0.38, fill=SLATE, r=0.03)
    c.circle(0.5, 0.6, 0.15, fill=DARK)
    c.circle(0.5, 0.6, 0.09, fill=mix(CYAN, WHITE, f))
    c.circle(0.78, 0.44, 0.03, fill=mix(RED, WHITE, f))
    if f:
        for k in range(10):
            a = k * TAU / 10
            c.line([(0.5 + 0.2 * math.cos(a), 0.6 + 0.2 * math.sin(a)),
                    (0.5 + 0.46 * math.cos(a), 0.6 + 0.46 * math.sin(a))], fill=fade(WHITE, 0.7), w=0.02)

# =================================================================== SPORT
@scene("bouncing football")
def _(c, t):
    y = 0.72 - abs(math.sin(t * math.pi)) * 0.44
    squash = 1 + 0.16 * max(0, math.cos(t * math.pi)) if y > 0.66 else 1
    ground(c)
    c.ellipse(0.5, y, 0.16 * squash, 0.16 / squash, fill=WHITE)
    a = t * TAU
    c.poly(rot(star_pts(0.5, y, 0.075, 5, 0.52), 0.5, y, a), fill=DARK)
    for k in range(5):
        aa = a + k * TAU / 5
        c.poly(rot(star_pts(0.5 + 0.115 * math.cos(aa), y + 0.115 * math.sin(aa), 0.03, 5, 0.5), 0.5, y, 0), fill=DARK)

@scene("basketball hoop")
def _(c, t):
    c.rect(0.55, 0.1, 0.95, 0.42, fill=WHITE, r=0.03)
    c.rect(0.63, 0.22, 0.87, 0.38, fill=None, outline=RED, w=0.018)
    c.line([(0.55, 0.42), (0.8, 0.42)], fill=RED, w=0.024)
    for k in range(5):
        x = 0.57 + k * 0.056
        c.line([(x, 0.43), (0.68 + (x - 0.68) * 0.4, 0.56)], fill=WHITE, w=0.008)
    f = t
    x = 0.18 + f * 0.5
    y = 0.8 - math.sin(f * math.pi) * 0.62
    c.circle(x, y, 0.095, fill=AMBER)
    c.arc(x, y, 0.095, 200, 340, DARK, w=0.01)
    c.line([(x - 0.095, y), (x + 0.095, y)], fill=DARK, w=0.01)

@scene("tennis rally")
def _(c, t):
    for px, col in ((0.12, RED), (0.88, CYAN)):           # bat: head plus handle
        c.ellipse(px, 0.46, 0.085, 0.13, fill=col)
        c.ellipse(px, 0.46, 0.058, 0.098, fill=mix(col, DARK, 0.55))
        c.rect(px - 0.025, 0.58, px + 0.025, 0.76, fill=mix(col, DARK, 0.3), r=0.02)
    f = abs(math.sin(t * math.pi))
    x = 0.24 + f * 0.52
    y = 0.5 - math.sin(f * math.pi) * 0.26
    for k in range(4):                                    # motion trail
        c.circle(x - (0.05 * k) * (1 if math.cos(t * math.pi) > 0 else -1), y, 0.06 * (1 - k * 0.2),
                 fill=fade(GREEN, 0.9 - k * 0.22))
    c.circle(x, y, 0.065, fill=GREEN)
    ground(c, 0.94, DARK)

@scene("bullseye")
def _(c, t):
    for i, col in enumerate([WHITE, RED, WHITE, RED]):
        c.circle(0.5, 0.5, 0.36 - i * 0.09, fill=col)
    f = min(1, t * 2.2)
    x = 0.5 + (1 - f) * 0.45
    y = 0.5 - (1 - f) * 0.4
    c.line([(x + 0.2, y - 0.18), (x, y)], fill=SLATE, w=0.02)
    c.poly([(x, y), (x + 0.07, y - 0.03), (x + 0.05, y - 0.07)], fill=AMBER)
    if f >= 1:
        c.circle(0.5, 0.5, 0.03 + 0.02 * math.sin(t * TAU * 3), fill=AMBER)

@scene("splash")
def _(c, t):
    c.rect(0, 0.66, 1, 1, fill=CYAN)
    if t < 0.25:
        c.circle(0.5, 0.1 + t * 2.2, 0.07, fill=WHITE)
    else:
        g = (t - 0.25) / 0.75
        for sgn in (-1, 1):                               # crown of water
            c.poly([(0.5 + sgn * 0.06, 0.68), (0.5 + sgn * (0.1 + g * 0.24), 0.66 - g * 0.34),
                    (0.5 + sgn * (0.18 + g * 0.26), 0.68)], fill=fade(WHITE, 1 - g * 0.5))
        c.ellipse(0.5, 0.68, 0.1 + g * 0.36, 0.024 + g * 0.08, outline=WHITE, w=0.02)
        for k in range(7):
            a = math.pi + 0.35 + k * (math.pi - 0.7) / 6
            r = g * 0.4
            c.circle(0.5 + r * math.cos(a) * 1.25, 0.62 + r * math.sin(a) + g * g * 0.34,
                     0.045 * (1 - g * 0.4), fill=fade(WHITE, 1 - g * 0.6))

@scene("trophy")
def _(c, t):
    sh = math.sin(t * TAU * 2) * 0.02
    c.arc(0.28, 0.34, 0.12, 90, 270, AMBER, w=0.03)
    c.arc(0.72, 0.34, 0.12, 270, 90, AMBER, w=0.03)
    c.poly([(0.3, 0.22), (0.7, 0.22), (0.62, 0.6), (0.38, 0.6)], fill=AMBER)
    c.rect(0.45, 0.6, 0.55, 0.74, fill=AMBER)
    c.rect(0.33, 0.74, 0.67, 0.84, fill=mix(AMBER, BROWN, 0.4), r=0.02)
    sparkle(c, 0.36 + sh, 0.3, 0.045, fade(WHITE, 0.4 + 0.6 * math.sin(t * TAU)))
    sparkle(c, 0.66 - sh, 0.42, 0.03, fade(WHITE, 0.4 + 0.6 * math.sin(t * TAU + 2)))

@scene("chequered flag")
def _(c, t):
    c.line([(0.2, 0.16), (0.2, 0.92)], fill=SLATE, w=0.026)
    n = 6
    for r in range(n):
        for col in range(n):
            x0 = 0.22 + col * 0.11
            wv = math.sin(t * TAU + col * 0.9) * 0.035
            y0 = 0.22 + r * 0.09 + wv
            c.rect(x0, y0, x0 + 0.11, y0 + 0.09, fill=WHITE if (r + col) % 2 else DARK)

@scene("dumbbell")
def _(c, t):
    y = 0.5 - abs(math.sin(t * math.pi)) * 0.12
    c.rect(0.3, y - 0.035, 0.7, y + 0.035, fill=SLATE, r=0.02)
    for x in (0.24, 0.76):
        c.rect(x - 0.1, y - 0.15, x + 0.1, y + 0.15, fill=WHITE, r=0.05)
        c.rect(x - 0.05, y - 0.19, x + 0.05, y + 0.19, fill=CYAN, r=0.04)

@scene("pool balls")
def _(c, t):
    f = min(1, t * 2)
    x1 = 0.12 + f * 0.28
    hit = t > 0.5
    x2 = 0.62 + (t - 0.5) * 0.7 if hit else 0.62
    c.rect(0, 0, 1, 1, fill=(16, 60, 44))
    c.circle(x1, 0.5, 0.1, fill=WHITE)
    c.circle(min(0.9, x2), 0.5, 0.1, fill=RED)
    c.circle(min(0.9, x2), 0.5, 0.045, fill=WHITE)
    if hit:
        for k in range(6):
            a = -0.8 + k * 0.32
            c.line([(0.52, 0.5), (0.52 + 0.08 * math.cos(a), 0.5 + 0.08 * math.sin(a))], fill=fade(WHITE, 1 - (t - 0.5) * 2), w=0.01)

# ==================================================================== FOOD
@scene("coffee")
def _(c, t):
    for i in range(3):
        f = (t + i * 0.33) % 1
        x = 0.5 + math.sin(f * 6 + i) * 0.035
        c.circle(x, 0.32 - f * 0.16, 0.028 + f * 0.02, fill=fade(WHITE, (1 - f) * 0.5))
    c.rect(0.28, 0.4, 0.66, 0.78, fill=WHITE, r=0.05)
    c.arc(0.7, 0.55, 0.11, -80, 80, WHITE, w=0.038)
    c.rect(0.31, 0.43, 0.63, 0.53, fill=BROWN, r=0.03)
    c.rect(0.22, 0.78, 0.72, 0.85, fill=SLATE, r=0.03)

@scene("pizza slice")
def _(c, t):
    lift = math.sin(t * TAU) * 0.03
    c.poly([(0.5, 0.1 + lift), (0.9, 0.86 + lift), (0.1, 0.86 + lift)], fill=AMBER)
    c.poly([(0.5, 0.2 + lift), (0.82, 0.84 + lift), (0.18, 0.84 + lift)], fill=mix(AMBER, WHITE, 0.45))
    for x, y in [(0.5, 0.42), (0.36, 0.66), (0.64, 0.66), (0.5, 0.76)]:
        c.circle(x, y + lift, 0.05, fill=RED)
    for k in range(3):
        f = (t * 1.5 + k * 0.33) % 1
        c.line([(0.62 + k * 0.06, 0.86 + lift), (0.62 + k * 0.06 + f * 0.1, 0.86 + lift + f * 0.1)],
               fill=fade(mix(AMBER, WHITE, 0.6), 1 - f), w=0.012)

@scene("popcorn")
def _(c, t):
    c.rect(0.26, 0.5, 0.74, 0.94, fill=RED, r=0.03)
    for k in range(4):
        c.rect(0.29 + k * 0.12, 0.5, 0.33 + k * 0.12, 0.94, fill=WHITE)
    for i in range(7):
        f = (t + i * 0.143) % 1
        x = 0.5 + math.sin(i * 2.4) * 0.3
        y = 0.52 - math.sin(f * math.pi) * 0.42
        c.circle(x, y, 0.05, fill=mix(WHITE, AMBER, 0.25))
        c.circle(x - 0.03, y - 0.02, 0.032, fill=WHITE)
        c.circle(x + 0.03, y + 0.02, 0.028, fill=WHITE)

@scene("birthday cake")
def _(c, t):
    c.rect(0.16, 0.56, 0.84, 0.86, fill=PINK, r=0.04)
    c.rect(0.16, 0.56, 0.84, 0.64, fill=WHITE, r=0.03)
    for k in range(3):
        x = 0.33 + k * 0.17
        c.rect(x - 0.018, 0.4, x + 0.018, 0.57, fill=CYAN)
        flame(c, x, 0.35, 0.05, t + k * 0.3)
    ground(c, 0.86, SLATE)

@scene("ice cream")
def _(c, t):
    c.poly([(0.34, 0.5), (0.66, 0.5), (0.5, 0.94)], fill=BROWN)
    c.circle(0.5, 0.42, 0.19, fill=PINK)
    c.circle(0.42, 0.3, 0.12, fill=mix(WHITE, CYAN, 0.3))
    for k in range(3):
        f = (t + k * 0.33) % 1
        c.circle(0.33 + k * 0.17, 0.52 + f * 0.3, 0.022 * (1 - f * 0.5), fill=fade(PINK, 1 - f * 0.6))

@scene("toast popping")
def _(c, t):
    y = 0.62 - max(0, math.sin(t * TAU)) * 0.4
    c.rect(0.36, y - 0.16, 0.64, y + 0.14, fill=mix(AMBER, BROWN, 0.35), r=0.04)
    c.rect(0.28, 0.56, 0.72, 0.9, fill=SLATE, r=0.06)
    c.rect(0.34, 0.56, 0.66, 0.6, fill=DARK, r=0.02)
    c.circle(0.66, 0.76, 0.03, fill=RED)

@scene("frying egg")
def _(c, t):
    c.circle(0.5, 0.56, 0.34, fill=DARK)
    c.rect(0.78, 0.52, 0.98, 0.6, fill=SLATE, r=0.03)
    c.ellipse(0.5, 0.56, 0.27, 0.22, fill=WHITE)
    c.circle(0.52, 0.55, 0.1, fill=AMBER)
    for k in range(4):
        f = (t + k * 0.25) % 1
        c.circle(0.34 + k * 0.11, 0.36 - f * 0.16, 0.018, fill=fade(WHITE, (1 - f) * 0.5))

@scene("cocktail")
def _(c, t):
    c.poly([(0.22, 0.28), (0.78, 0.28), (0.5, 0.62)], fill=WHITE)
    c.poly([(0.27, 0.33), (0.73, 0.33), (0.5, 0.58)], fill=mix(PINK, RED, 0.3))
    c.rect(0.48, 0.62, 0.52, 0.86, fill=WHITE)
    c.rect(0.34, 0.86, 0.66, 0.91, fill=WHITE, r=0.02)
    c.line([(0.62, 0.2), (0.44, 0.5)], fill=CYAN, w=0.018)
    c.circle(0.3, 0.32, 0.06, fill=AMBER)
    for k in range(3):
        f = (t + k * 0.33) % 1
        c.circle(0.44 + k * 0.05, 0.55 - f * 0.18, 0.016, fill=fade(WHITE, 1 - f))

@scene("doughnut")
def _(c, t):
    a = t * TAU
    c.circle(0.5, 0.5, 0.32, fill=mix(AMBER, BROWN, 0.3))
    c.circle(0.5, 0.5, 0.3, fill=PINK)
    c.circle(0.5, 0.5, 0.1, fill=BG)
    for k in range(10):
        aa = a + k * TAU / 10
        r = 0.2 if k % 2 else 0.15
        c.rect(0.5 + r * math.cos(aa) - 0.02, 0.5 + r * math.sin(aa) - 0.008,
               0.5 + r * math.cos(aa) + 0.02, 0.5 + r * math.sin(aa) + 0.008,
               fill=[CYAN, AMBER, WHITE, GREEN, RED][k % 5], r=0.006)

@scene("kettle steam")
def _(c, t):
    for i in range(4):
        f = (t + i * 0.25) % 1
        x = 0.72 + math.sin(f * 7 + i) * 0.05
        c.circle(x, 0.4 - f * 0.28, 0.03 + f * 0.02, fill=fade(WHITE, (1 - f) * 0.55))
    c.ellipse(0.45, 0.68, 0.3, 0.24, fill=WHITE)
    c.poly([(0.68, 0.58), (0.82, 0.42), (0.76, 0.4), (0.64, 0.54)], fill=WHITE)
    c.arc(0.45, 0.42, 0.2, 190, 350, SLATE, w=0.026)
    c.rect(0.3, 0.9, 0.6, 0.94, fill=SLATE, r=0.02)

# ================================================================= ANIMALS
@scene("fish")
def _(c, t):
    x = 0.15 + t * 0.6
    wag = math.sin(t * TAU * 3) * 0.06
    c.ellipse(x, 0.5, 0.16, 0.1, fill=CYAN)
    c.poly([(x - 0.15, 0.5), (x - 0.3, 0.42 + wag), (x - 0.3, 0.58 + wag)], fill=mix(CYAN, PURPLE, 0.4))
    c.circle(x + 0.09, 0.47, 0.022, fill=WHITE)
    for k in range(3):
        f = (t * 2 + k * 0.33) % 1
        c.circle(x + 0.2 + f * 0.12, 0.42 - f * 0.16, 0.016 * (1 - f * 0.4), fill=fade(WHITE, 1 - f))

@scene("butterfly")
def _(c, t):
    y = 0.5 + math.sin(t * TAU) * 0.1
    flap = 0.55 + 0.45 * abs(math.sin(t * TAU * 2))
    for sgn in (-1, 1):
        c.ellipse(0.5 + sgn * 0.16 * flap, y - 0.07, 0.15 * flap, 0.12, fill=PINK)
        c.ellipse(0.5 + sgn * 0.13 * flap, y + 0.09, 0.11 * flap, 0.09, fill=PURPLE)
    c.ellipse(0.5, y, 0.025, 0.14, fill=WHITE)
    c.line([(0.5, y - 0.13), (0.44, y - 0.22)], fill=WHITE, w=0.01)
    c.line([(0.5, y - 0.13), (0.56, y - 0.22)], fill=WHITE, w=0.01)

@scene("bird flying")
def _(c, t):
    for i, (bx, by, sc, ph) in enumerate([(0.5, 0.45, 1.0, 0.0), (0.24, 0.66, 0.62, 0.4), (0.76, 0.7, 0.55, 0.7)]):
        f = math.sin((t + ph) * TAU)
        y = by + f * 0.03
        w = 0.18 * sc
        c.line([(bx - w, y + f * w * 0.5), (bx, y), (bx + w, y + f * w * 0.5)], fill=WHITE, w=0.022 * sc)

@scene("jellyfish")
def _(c, t):
    y = 0.4 + math.sin(t * TAU) * 0.06
    sq = 1 + 0.12 * math.sin(t * TAU)
    c.ellipse(0.5, y, 0.24 * sq, 0.2 / sq, fill=fade(PINK, 0.9))
    c.rect(0.26, y, 0.74, y + 0.06, fill=fade(PINK, 0.9))
    for k in range(5):
        x = 0.32 + k * 0.09
        pts = [(x + math.sin(t * TAU + k + j * 0.7) * 0.03, y + 0.06 + j * 0.08) for j in range(5)]
        c.line(pts, fill=fade(PURPLE, 0.85), w=0.014)

@scene("bee")
def _(c, t):
    x = 0.5 + math.sin(t * TAU) * 0.26
    y = 0.5 + math.sin(t * TAU * 2) * 0.14
    c.ellipse(x, y, 0.14, 0.1, fill=AMBER)
    for k in range(3):
        c.rect(x - 0.09 + k * 0.07, y - 0.095, x - 0.055 + k * 0.07, y + 0.095, fill=DARK)
    c.circle(x + 0.14, y - 0.02, 0.06, fill=DARK)
    fl = abs(math.sin(t * TAU * 4))
    c.ellipse(x - 0.02, y - 0.14, 0.08, 0.05 * fl + 0.02, fill=fade(WHITE, 0.7))
    for k in range(6):
        f = (t + k / 6) % 1
        c.circle(x - 0.2 - f * 0.1, y + math.sin(f * 9) * 0.06, 0.008, fill=fade(WHITE, (1 - f) * 0.4))

@scene("snail")
def _(c, t):
    x = 0.2 + t * 0.42
    c.ellipse(x + 0.16, 0.74, 0.14, 0.07, fill=mix(WHITE, AMBER, 0.4))
    c.circle(x + 0.24, 0.66, 0.055, fill=mix(WHITE, AMBER, 0.4))
    c.line([(x + 0.24, 0.62), (x + 0.27, 0.54)], fill=mix(WHITE, AMBER, 0.4), w=0.012)
    c.circle(x + 0.275, 0.53, 0.018, fill=DARK)
    for k in range(4):
        c.arc(x, 0.68, 0.13 - k * 0.03, 0, 360, mix(BROWN, AMBER, 0.4 + k * 0.12), w=0.024)
    ground(c, 0.82, SLATE)

@scene("spider drop")
def _(c, t):
    y = 0.2 + abs(math.sin(t * math.pi)) * 0.45
    c.line([(0.5, 0), (0.5, y)], fill=WHITE, w=0.008)
    c.circle(0.5, y + 0.1, 0.1, fill=DARK)
    c.circle(0.5, y + 0.02, 0.06, fill=DARK)
    for sgn in (-1, 1):
        for k in range(3):
            a = 0.5 + k * 0.5
            c.line([(0.5, y + 0.08), (0.5 + sgn * 0.16, y + 0.02 + k * 0.07),
                    (0.5 + sgn * 0.24, y + 0.12 + k * 0.06)], fill=DARK, w=0.014)
    c.circle(0.47, y - 0.01, 0.016, fill=RED)
    c.circle(0.53, y - 0.01, 0.016, fill=RED)

@scene("snake")
def _(c, t):
    pts = [(0.1 + i / 24 * 0.8, 0.5 + math.sin(i / 24 * 9 + t * TAU) * 0.18) for i in range(25)]
    c.line(pts, fill=GREEN, w=0.09)
    hx, hy = pts[-1]
    c.circle(hx, hy, 0.06, fill=GREEN)
    c.circle(hx + 0.02, hy - 0.025, 0.014, fill=WHITE)
    c.line([(hx + 0.05, hy + 0.01), (hx + 0.12, hy + 0.01)], fill=RED, w=0.01)

@scene("crab")
def _(c, t):
    x = 0.5 + math.sin(t * TAU) * 0.16
    c.ellipse(x, 0.58, 0.2, 0.14, fill=RED)
    for sgn in (-1, 1):
        for k in range(3):
            c.line([(x + sgn * 0.16, 0.6 + k * 0.04), (x + sgn * 0.28, 0.68 + k * 0.05)], fill=RED, w=0.018)
        cl = 0.08 + 0.03 * math.sin(t * TAU * 2 + (0 if sgn > 0 else 1.6))
        c.circle(x + sgn * 0.28, 0.44, cl, fill=RED)
        c.circle(x + sgn * 0.06, 0.46, 0.03, fill=WHITE)
        c.circle(x + sgn * 0.06, 0.46, 0.014, fill=DARK)
    ground(c, 0.8, mix(AMBER, WHITE, 0.4))

@scene("paw prints")
def _(c, t):
    for i in range(5):
        f = (t + i * 0.2) % 1
        x = 0.16 + i * 0.17
        y = 0.66 - i * 0.1
        col = fade(PINK, 1 - f * 0.75)
        c.ellipse(x, y + 0.012, 0.075, 0.085, fill=col)
        for k in range(4):
            a = -2.55 + k * 0.6
            c.ellipse(x + 0.1 * math.cos(a), y - 0.02 + 0.1 * math.sin(a), 0.03, 0.036, fill=col)

# =============================================================== TRANSPORT
@scene("car driving")
def _(c, t):
    ground(c, 0.82, SLATE)
    for k in range(5):
        x = (0.1 + k * 0.25 - t * 0.5) % 1.2 - 0.1
        c.rect(x, 0.9, x + 0.12, 0.93, fill=WHITE, r=0.01)
    b = math.sin(t * TAU * 3) * 0.006
    c.rect(0.18, 0.56 + b, 0.82, 0.74 + b, fill=RED, r=0.05)
    c.poly([(0.32, 0.56 + b), (0.66, 0.56 + b), (0.6, 0.42 + b), (0.38, 0.42 + b)], fill=CYAN)
    for x in (0.32, 0.68):
        c.circle(x, 0.78, 0.075, fill=DARK)
        c.circle(x, 0.78, 0.032, fill=WHITE)

@scene("traffic light")
def _(c, t):
    step = int(t * 3) % 3
    c.rect(0.36, 0.1, 0.64, 0.86, fill=SLATE, r=0.06)
    c.rect(0.46, 0.86, 0.54, 1.0, fill=DARK)
    for i, col in enumerate([RED, AMBER, GREEN]):
        c.circle(0.5, 0.24 + i * 0.24, 0.078, fill=col if i == step else DARK)

@scene("train")
def _(c, t):
    ground(c, 0.86, SLATE)
    x = -0.15 + t * 0.4
    for k in range(4):
        c.rect(x + k * 0.3, 0.5, x + 0.26 + k * 0.3, 0.8, fill=CYAN if k else RED, r=0.04)
        c.rect(x + 0.03 + k * 0.3, 0.55, x + 0.12 + k * 0.3, 0.65, fill=WHITE, r=0.02)
        c.circle(x + 0.07 + k * 0.3, 0.83, 0.04, fill=DARK)
        c.circle(x + 0.2 + k * 0.3, 0.83, 0.04, fill=DARK)
    for k in range(3):
        f = (t * 2 + k * 0.33) % 1
        c.circle(x + 0.06, 0.42 - f * 0.28, 0.03 + f * 0.03, fill=fade(WHITE, (1 - f) * 0.5))

@scene("aeroplane")
def _(c, t):
    x = 0.12 + t * 0.66
    y = 0.62 - t * 0.24
    c.poly([(x + 0.22, y), (x - 0.14, y - 0.05), (x - 0.14, y + 0.05)], fill=WHITE)
    c.poly([(x + 0.02, y), (x - 0.1, y - 0.2), (x - 0.02, y - 0.2)], fill=mix(WHITE, CYAN, 0.5))
    c.poly([(x + 0.02, y), (x - 0.1, y + 0.2), (x - 0.02, y + 0.2)], fill=mix(WHITE, CYAN, 0.5))
    for k in range(6):
        f = k / 6
        c.circle(x - 0.2 - f * 0.28, y + 0.04 + f * 0.05, 0.022 * (1 - f), fill=fade(WHITE, (1 - f) * 0.45))

@scene("sailing boat")
def _(c, t):
    base = 0.72
    pts = [(x / 24, base + 0.06 + math.sin(x / 24 * 7 + t * TAU) * 0.03) for x in range(25)]
    tilt = math.sin(t * TAU) * 0.05
    y = base + math.sin(t * TAU) * 0.02
    c.poly(rot([(0.5, y - 0.42), (0.5, y - 0.04), (0.78, y - 0.04)], 0.5, y, tilt), fill=WHITE)
    c.poly(rot([(0.46, y - 0.4), (0.46, y - 0.04), (0.24, y - 0.04)], 0.5, y, tilt), fill=CYAN)
    c.poly(rot([(0.18, y - 0.02), (0.82, y - 0.02), (0.68, y + 0.12), (0.32, y + 0.12)], 0.5, y, tilt), fill=RED)
    c.poly(pts + [(1, 1), (0, 1)], fill=mix(CYAN, DARK, 0.55))

@scene("hot air balloon")
def _(c, t):
    y = 0.44 + math.sin(t * TAU) * 0.05
    for i, col in enumerate([RED, AMBER, CYAN]):
        c.pie(0.5, y, 0.24, -180 + i * 60, -120 + i * 60, col)
        c.pie(0.5, y, 0.24, i * 60, 60 + i * 60, col)
    c.poly([(0.34, y + 0.16), (0.66, y + 0.16), (0.58, y + 0.28), (0.42, y + 0.28)], fill=mix(RED, AMBER, 0.5))
    c.line([(0.42, y + 0.28), (0.44, y + 0.38)], fill=WHITE, w=0.008)
    c.line([(0.58, y + 0.28), (0.56, y + 0.38)], fill=WHITE, w=0.008)
    c.rect(0.42, 0.36 + y, 0.58, 0.46 + y, fill=BROWN, r=0.02)

@scene("bicycle wheel")
def _(c, t):
    a = t * TAU
    for x in (0.28, 0.72):
        c.circle(x, 0.62, 0.2, outline=WHITE, w=0.022)
        for k in range(8):
            aa = a + k * TAU / 8
            c.line([(x, 0.62), (x + 0.19 * math.cos(aa), 0.62 + 0.19 * math.sin(aa))], fill=SLATE, w=0.008)
        c.circle(x, 0.62, 0.03, fill=WHITE)
    c.line([(0.28, 0.62), (0.46, 0.4), (0.72, 0.62)], fill=CYAN, w=0.02)
    c.line([(0.46, 0.4), (0.4, 0.62), (0.28, 0.62)], fill=CYAN, w=0.02)
    c.line([(0.44, 0.34), (0.56, 0.34)], fill=WHITE, w=0.018)
    ground(c, 0.84, SLATE)

@scene("submarine")
def _(c, t):
    c.rect(0, 0, 1, 1, fill=(12, 40, 74))
    y = 0.56 + math.sin(t * TAU) * 0.04
    x = 0.16 + t * 0.2
    c.ellipse(x + 0.24, y, 0.26, 0.13, fill=AMBER)
    c.rect(x + 0.18, y - 0.24, x + 0.3, y - 0.1, fill=AMBER, r=0.02)
    c.line([(x + 0.24, y - 0.24), (x + 0.24, y - 0.34)], fill=AMBER, w=0.014)
    c.poly([(x - 0.02, y), (x - 0.12, y - 0.1), (x - 0.12, y + 0.1)], fill=mix(AMBER, BROWN, 0.4))
    c.circle(x + 0.32, y, 0.05, fill=CYAN)
    for k in range(5):
        f = (t + k * 0.2) % 1
        c.circle(x - 0.16 - f * 0.14, y - f * 0.2, 0.016 * (1 - f * 0.5), fill=fade(WHITE, (1 - f) * 0.5))

# ============================================================ PARTY / MOOD
@scene("heartbeat")
def _(c, t):
    k = 1 + 0.14 * max(0, math.sin(t * TAU * 2)) ** 3 + 0.07 * max(0, math.sin(t * TAU * 2 - 0.6)) ** 3
    heart(c, 0.5, 0.46, 0.2 * k, RED)
    pts = []
    for i in range(31):
        x = i / 30
        s = (x - ((t * 1.0) % 1))
        y = 0.86
        if -0.06 < s < 0.06:
            y = 0.86 - math.sin((s + 0.06) / 0.12 * math.pi) * 0.12 * (1 if s < 0 else -1)
        pts.append((x, y))
    c.line(pts, fill=fade(RED, 0.8), w=0.012)

@scene("broken heart")
def _(c, t):
    g = t
    for sgn in (-1, 1):
        off = sgn * g * 0.1
        c.circle(0.5 + sgn * 0.1 + off, 0.4, 0.11, fill=mix(RED, DARK, 0.15))
        c.poly([(0.5 + off, 0.34), (0.5 + sgn * 0.21 + off, 0.34), (0.5 + off * 1.4, 0.68)], fill=mix(RED, DARK, 0.15))
    c.line([(0.5, 0.3), (0.46, 0.44), (0.54, 0.52), (0.5, 0.68)], fill=BG, w=0.03)

@scene("confetti")
def _(c, t):
    cols = [PINK, CYAN, AMBER, GREEN, PURPLE, RED]
    for i in range(22):
        f = (t + i * 0.045) % 1
        x = (i * 0.137) % 1
        y = f * 1.05 - 0.05
        a = f * 9 + i
        c.poly(rot([(x - 0.022, y - 0.012), (x + 0.022, y - 0.012), (x + 0.022, y + 0.012), (x - 0.022, y + 0.012)],
                   x, y, a), fill=cols[i % 6])

@scene("balloon")
def _(c, t):
    y = 0.42 + math.sin(t * TAU) * 0.05
    sway = math.sin(t * TAU) * 0.03
    c.ellipse(0.5, y, 0.2, 0.24, fill=RED)
    c.poly([(0.47, y + 0.23), (0.53, y + 0.23), (0.5, y + 0.29)], fill=RED)
    pts = [(0.5 + math.sin(k * 1.2 + t * TAU) * 0.03 + sway * k / 6, y + 0.29 + k * 0.06) for k in range(7)]
    c.line(pts, fill=WHITE, w=0.008)
    c.ellipse(0.43, y - 0.09, 0.05, 0.07, fill=fade(WHITE, 0.35))

@scene("thumbs up")
def _(c, t):
    y = 0.56 - abs(math.sin(t * math.pi)) * 0.06
    c.rect(0.34, y - 0.02, 0.72, y + 0.26, fill=AMBER, r=0.06)
    c.rect(0.22, y + 0.02, 0.36, y + 0.26, fill=mix(AMBER, BROWN, 0.25), r=0.04)
    c.rect(0.42, y - 0.24, 0.56, y + 0.04, fill=AMBER, r=0.06)
    for k in range(3):
        c.line([(0.46, y + 0.06 + k * 0.06), (0.68, y + 0.06 + k * 0.06)], fill=fade(BROWN, 0.5), w=0.008)
    if abs(math.sin(t * math.pi)) > 0.9:
        for k in range(5):
            a = -2.2 + k * 0.35
            c.line([(0.5 + 0.3 * math.cos(a), y - 0.2 + 0.3 * math.sin(a)),
                    (0.5 + 0.4 * math.cos(a), y - 0.2 + 0.4 * math.sin(a))], fill=AMBER, w=0.014)

@scene("wink")
def _(c, t):
    c.circle(0.5, 0.5, 0.34, fill=AMBER)
    c.circle(0.38, 0.42, 0.04, fill=DARK)
    if t < 0.45:
        c.circle(0.62, 0.42, 0.04, fill=DARK)
    else:
        c.line([(0.56, 0.43), (0.68, 0.43)], fill=DARK, w=0.026)
    c.arc(0.5, 0.48, 0.18, 20, 160, DARK, w=0.03)

@scene("crying")
def _(c, t):
    c.circle(0.5, 0.48, 0.34, fill=AMBER)
    c.arc(0.38, 0.36, 0.06, 200, 340, DARK, w=0.022)
    c.arc(0.62, 0.36, 0.06, 200, 340, DARK, w=0.022)
    c.arc(0.5, 0.72, 0.16, 200, 340, DARK, w=0.028)
    for k in range(2):
        f = (t + k * 0.5) % 1
        for x in (0.36, 0.64):
            drop(c, x, 0.5 + f * 0.42, 0.028 * (1 - f * 0.3), CYAN)

@scene("party popper")
def _(c, t):
    c.poly(rot([(0.16, 0.86), (0.3, 0.62), (0.42, 0.72)], 0.3, 0.76, 0), fill=AMBER)
    cols = [PINK, CYAN, GREEN, WHITE, PURPLE]
    for i in range(16):
        f = (t + i * 0.02) % 1
        a = -1.1 + (i % 8) * 0.13
        r = f * 0.9
        x = 0.36 + math.cos(a) * r
        y = 0.68 + math.sin(a) * r + f * f * 0.35
        c.poly(rot([(x - 0.02, y - 0.012), (x + 0.02, y - 0.012), (x + 0.02, y + 0.012), (x - 0.02, y + 0.012)],
                   x, y, f * 8 + i), fill=fade(cols[i % 5], 1 - f * 0.5))

# =========================================================== HOME AND MISC
@scene("dripping tap")
def _(c, t):
    c.rect(0.16, 0.2, 0.26, 0.5, fill=SLATE, r=0.02)
    c.rect(0.16, 0.2, 0.62, 0.3, fill=SLATE, r=0.03)
    c.rect(0.54, 0.28, 0.62, 0.42, fill=SLATE, r=0.02)
    c.circle(0.21, 0.16, 0.06, fill=CYAN)
    f = t
    if f < 0.75:
        drop(c, 0.58, 0.46 + f * 0.5, 0.03, CYAN)
    else:
        g = (f - 0.75) / 0.25
        c.ellipse(0.58, 0.9, 0.06 + g * 0.14, 0.012 + g * 0.02, outline=fade(CYAN, 1 - g), w=0.01)
    c.rect(0.36, 0.88, 0.8, 0.94, fill=DARK, r=0.02)

@scene("washing machine")
def _(c, t):
    c.rect(0.14, 0.1, 0.86, 0.92, fill=WHITE, r=0.07)
    c.rect(0.2, 0.16, 0.8, 0.24, fill=SLATE, r=0.02)
    c.circle(0.5, 0.58, 0.26, fill=SLATE)
    c.circle(0.5, 0.58, 0.21, fill=mix(CYAN, DARK, 0.4))
    a = t * TAU * 2
    for k in range(3):
        aa = a + k * TAU / 3
        c.circle(0.5 + 0.11 * math.cos(aa), 0.58 + 0.11 * math.sin(aa), 0.05, fill=[PINK, AMBER, GREEN][k])
    for k in range(4):
        f = (t + k * 0.25) % 1
        c.circle(0.5 + math.cos(f * TAU + k) * 0.15, 0.58 + math.sin(f * TAU + k) * 0.15, 0.018, fill=fade(WHITE, 0.6))

@scene("ceiling fan")
def _(c, t):
    a = t * TAU
    c.line([(0.5, 0.06), (0.5, 0.24)], fill=SLATE, w=0.026)
    for k in range(4):
        aa = a + k * TAU / 4
        c.poly(rot([(0.5, 0.24), (0.5 + 0.38, 0.2), (0.5 + 0.38, 0.3)], 0.5, 0.25, aa), fill=mix(BROWN, WHITE, 0.3))
    c.circle(0.5, 0.25, 0.06, fill=SLATE)

@scene("doorbell")
def _(c, t):
    push = 0.02 if (t % 0.5) < 0.15 else 0
    c.rect(0.32, 0.2, 0.68, 0.8, fill=SLATE, r=0.06)
    c.circle(0.5, 0.4 + push, 0.11, fill=RED if push else mix(RED, DARK, 0.4))
    for k in range(3):
        f = (t * 2 + k * 0.33) % 1
        c.arc(0.5, 0.4, 0.16 + f * 0.3, 200, 340, fade(AMBER, 1 - f), w=0.014)
    c.rect(0.38, 0.58, 0.62, 0.7, fill=WHITE, r=0.02)

@scene("light switch")
def _(c, t):
    on = t > 0.5
    c.rect(0, 0, 1, 1, fill=mix(BG, (60, 56, 30), 0.55 if on else 0))
    c.rect(0.32, 0.24, 0.68, 0.76, fill=WHITE, r=0.05)
    c.rect(0.42, 0.3 if on else 0.5, 0.58, 0.5 if on else 0.7, fill=AMBER if on else SLATE, r=0.03)
    if on:
        for k in range(8):
            a = k * TAU / 8
            c.line([(0.5 + 0.42 * math.cos(a), 0.5 + 0.42 * math.sin(a)),
                    (0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a))], fill=fade(AMBER, 0.5), w=0.016)

@scene("dice roll")
def _(c, t):
    face = int(t * 6) % 6 + 1
    hop = abs(math.sin(t * math.pi * 2)) * 0.06
    c.rect(0.28, 0.28 - hop, 0.72, 0.72 - hop, fill=WHITE, r=0.08)
    pips = {1: [(0.5, 0.5)], 2: [(0.38, 0.38), (0.62, 0.62)],
            3: [(0.38, 0.38), (0.5, 0.5), (0.62, 0.62)],
            4: [(0.38, 0.38), (0.62, 0.38), (0.38, 0.62), (0.62, 0.62)],
            5: [(0.38, 0.38), (0.62, 0.38), (0.5, 0.5), (0.38, 0.62), (0.62, 0.62)],
            6: [(0.38, 0.36), (0.62, 0.36), (0.38, 0.5), (0.62, 0.5), (0.38, 0.64), (0.62, 0.64)]}[face]
    for x, y in pips:
        c.circle(x, y - hop, 0.045, fill=DARK)
    c.ellipse(0.5, 0.78, 0.2 - hop, 0.03, fill=DARK)

@scene("coin flip")
def _(c, t):
    y = 0.6 - math.sin(t * math.pi) * 0.4
    w = abs(math.cos(t * TAU * 2))
    c.ellipse(0.5, y, max(0.012, 0.17 * w), 0.17, fill=AMBER)
    if w > 0.35:
        c.ellipse(0.5, y, 0.11 * w, 0.11, fill=mix(AMBER, BROWN, 0.35))
    ground(c, 0.86, SLATE)

@scene("juggling")
def _(c, t):
    cols = [RED, CYAN, AMBER]
    for i in range(3):
        f = (t + i / 3) % 1
        x = 0.5 + math.sin(f * TAU) * 0.26
        y = 0.62 - abs(math.sin(f * math.pi)) * 0.42
        c.circle(x, y, 0.07, fill=cols[i])
    c.circle(0.32, 0.78, 0.06, fill=WHITE)
    c.circle(0.68, 0.78, 0.06, fill=WHITE)

@scene("spinning top")
def _(c, t):
    lean = math.sin(t * TAU) * 0.08
    pts = rot([(0.5, 0.24), (0.68, 0.5), (0.5, 0.8), (0.32, 0.5)], 0.5, 0.5, lean)
    c.poly(pts, fill=CYAN)
    c.poly(rot([(0.5, 0.24), (0.58, 0.42), (0.42, 0.42)], 0.5, 0.5, lean), fill=WHITE)
    c.line(rot([(0.5, 0.2), (0.5, 0.1)], 0.5, 0.5, lean), fill=WHITE, w=0.016)
    c.ellipse(0.5, 0.86, 0.16, 0.03, fill=DARK)
    for k in range(3):
        f = (t * 2 + k * 0.33) % 1
        c.arc(0.5, 0.82, 0.08 + f * 0.2, 0, 360, fade(SLATE, 1 - f), w=0.008)

@scene("dominoes")
def _(c, t):
    for i in range(6):
        trigger = i * 0.14
        f = max(0.0, min(1.0, (t - trigger) / 0.16))
        a = f * 1.2
        x = 0.14 + i * 0.15
        c.poly(rot([(x - 0.03, 0.5), (x + 0.03, 0.5), (x + 0.03, 0.86), (x - 0.03, 0.86)], x, 0.86, a),
               fill=[WHITE, CYAN][i % 2])
    ground(c, 0.86, SLATE)

@scene("seesaw")
def _(c, t):
    a = math.sin(t * TAU) * 0.3
    c.poly([(0.5, 0.6), (0.62, 0.88), (0.38, 0.88)], fill=SLATE)
    c.poly(rot([(0.12, 0.56), (0.88, 0.56), (0.88, 0.63), (0.12, 0.63)], 0.5, 0.6, a), fill=WHITE)
    p1 = rot([(0.2, 0.5)], 0.5, 0.6, a)[0]
    p2 = rot([(0.8, 0.5)], 0.5, 0.6, a)[0]
    c.circle(p1[0], p1[1], 0.07, fill=RED)
    c.circle(p2[0], p2[1], 0.07, fill=CYAN)
    ground(c, 0.88, SLATE)

@scene("yo-yo")
def _(c, t):
    y = 0.24 + abs(math.sin(t * math.pi)) * 0.5
    c.line([(0.5, 0.08), (0.5, y)], fill=WHITE, w=0.008)
    c.circle(0.5, y, 0.13, fill=PURPLE)
    a = t * TAU * 3
    c.line([(0.5 + 0.1 * math.cos(a), y + 0.1 * math.sin(a)),
            (0.5 - 0.1 * math.cos(a), y - 0.1 * math.sin(a))], fill=WHITE, w=0.016)
    c.circle(0.5, 0.06, 0.03, fill=SLATE)

@scene("key turning")
def _(c, t):
    a = math.sin(t * TAU) * 0.9
    pts = rot([(0.34, 0.5), (0.78, 0.5)], 0.34, 0.5, a)
    c.line(pts, fill=AMBER, w=0.045)
    for k in (0.6, 0.72):
        p = rot([(k, 0.5), (k, 0.62)], 0.34, 0.5, a)
        c.line(p, fill=AMBER, w=0.03)
    c.circle(0.34, 0.5, 0.13, fill=AMBER)
    c.circle(0.34, 0.5, 0.06, fill=BG)

@scene("gears")
def _(c, t):
    def gear(cx, cy, r, teeth, a, col):
        for k in range(teeth):
            aa = a + k * TAU / teeth
            c.poly(rot([(cx + r * 0.92, cy - r * 0.18), (cx + r * 1.2, cy - r * 0.13),
                        (cx + r * 1.2, cy + r * 0.13), (cx + r * 0.92, cy + r * 0.18)], cx, cy, aa), fill=col)
        c.circle(cx, cy, r, fill=col)
        c.circle(cx, cy, r * 0.34, fill=BG)
    gear(0.36, 0.42, 0.19, 8, t * TAU / 8, CYAN)
    gear(0.68, 0.66, 0.14, 6, -t * TAU / 6 + 0.3, AMBER)

@scene("magnet")
def _(c, t):
    c.arc(0.5, 0.52, 0.24, 180, 360, SLATE, w=0.13)
    c.rect(0.2, 0.52, 0.33, 0.74, fill=RED, r=0.01)
    c.rect(0.67, 0.52, 0.8, 0.74, fill=RED, r=0.01)
    for k in range(3):
        f = (t + k * 0.33) % 1
        c.arc(0.5, 0.3, 0.1 + f * 0.24, 200, 340, fade(CYAN, 1 - f), w=0.014)
    c.circle(0.5 + math.sin(t * TAU) * 0.04, 0.16, 0.035, fill=WHITE)

@scene("countdown")
def _(c, t):
    c.circle(0.5, 0.5, 0.3, outline=SLATE, w=0.02)
    for k in range(12):
        a = k * TAU / 12
        lit = (k / 12) < t
        c.circle(0.5 + 0.24 * math.cos(a - 1.57), 0.5 + 0.24 * math.sin(a - 1.57), 0.035,
                 fill=AMBER if lit else DARK)

@scene("snake game")
def _(c, t):
    for gx in range(6):
        for gy in range(6):
            c.rect(0.1 + gx * 0.135, 0.1 + gy * 0.135, 0.21 + gx * 0.135, 0.21 + gy * 0.135, fill=(24, 28, 56), r=0.01)
    path = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (4, 1), (4, 2), (3, 2), (2, 2), (1, 2),
            (1, 3), (1, 4), (2, 4), (3, 4), (4, 4), (5, 4), (5, 5)]
    head = int(t * len(path)) % len(path)
    for i in range(5):
        k = (head - i) % len(path)
        gx, gy = path[k]
        c.rect(0.1 + gx * 0.135, 0.1 + gy * 0.135, 0.21 + gx * 0.135, 0.21 + gy * 0.135,
               fill=mix(GREEN, DARK, i * 0.15), r=0.02)
    c.circle(0.1 + 5 * 0.135 + 0.055, 0.1 + 1 * 0.135 + 0.055, 0.04, fill=RED)

@scene("ripples")
def _(c, t):
    for k in range(4):
        f = (t + k / 4) % 1
        c.circle(0.5, 0.5, 0.04 + f * 0.42, outline=fade(CYAN, 1 - f), w=0.016)

@scene("bouncing ball")
def _(c, t):
    y = 0.74 - abs(math.sin(t * math.pi)) * 0.5
    sq = 1 + 0.22 * max(0, math.cos(t * math.pi)) if y > 0.68 else 1
    ground(c)
    c.ellipse(0.5, y, 0.15 * sq, 0.15 / sq, fill=PINK)
    c.circle(0.45, y - 0.05, 0.035, fill=fade(WHITE, 0.45))

@scene("stairs")
def _(c, t):
    for i in range(5):
        c.rect(0.08 + i * 0.17, 0.78 - i * 0.13, 0.28 + i * 0.17, 0.92, fill=mix(SLATE, WHITE, i * 0.12))
    f = t
    i = min(4, int(f * 5))
    x = 0.18 + i * 0.17
    y = 0.72 - i * 0.13 - abs(math.sin(f * 5 * math.pi)) * 0.06
    c.circle(x, y, 0.06, fill=RED)

@scene("latte art")
def _(c, t):
    c.circle(0.5, 0.52, 0.3, fill=WHITE)
    c.circle(0.5, 0.52, 0.25, fill=BROWN)
    a = t * TAU
    for k in range(3):
        aa = a + k * TAU / 3
        pts = [(0.5 + (0.04 + j * 0.03) * math.cos(aa + j * 0.7),
                0.52 + (0.04 + j * 0.03) * math.sin(aa + j * 0.7)) for j in range(6)]
        c.line(pts, fill=fade(WHITE, 0.5), w=0.012)

@scene("padlock unlocking")
def _(c, t):
    lift = t * 0.07
    c.arc(0.5 + t * 0.06, 0.4 - lift, 0.15, 180, 360, WHITE, w=0.042)
    c.line([(0.35 + t * 0.06, 0.4 - lift), (0.35 + t * 0.06, 0.52)], fill=WHITE, w=0.042)
    c.line([(0.65 + t * 0.06, 0.4 - lift), (0.65 + t * 0.06, 0.5)], fill=WHITE, w=0.042)
    c.rect(0.28, 0.5, 0.72, 0.86, fill=GREEN, r=0.06)
    c.circle(0.5, 0.66, 0.05, fill=DARK)

@scene("thermometer")
def _(c, t):
    lvl = 0.2 + 0.55 * (0.5 + 0.5 * math.sin(t * TAU))
    c.rect(0.44, 0.12, 0.56, 0.76, fill=WHITE, r=0.06)
    c.circle(0.5, 0.8, 0.13, fill=WHITE)
    c.circle(0.5, 0.8, 0.09, fill=RED)
    c.rect(0.47, 0.8 - lvl, 0.53, 0.8, fill=RED, r=0.03)
    for k in range(5):
        c.line([(0.57, 0.24 + k * 0.11), (0.63, 0.24 + k * 0.11)], fill=SLATE, w=0.01)

@scene("umbrella")
def _(c, t):
    sway = math.sin(t * TAU) * 0.02
    for i in range(9):
        x = 0.1 + i * 0.1
        f = (t + i * 0.11) % 1
        c.line([(x, 0.1 + f * 0.3), (x - 0.015, 0.16 + f * 0.3)], fill=CYAN, w=0.012)
    c.pie(0.5 + sway, 0.56, 0.36, 180, 360, RED)
    for k in range(4):
        c.line([(0.14 + sway + k * 0.24, 0.56), (0.26 + sway + k * 0.24, 0.56)], fill=mix(RED, DARK, 0.3), w=0.012)
    c.line([(0.5 + sway, 0.56), (0.5 + sway, 0.86)], fill=WHITE, w=0.016)
    c.arc(0.44 + sway, 0.86, 0.06, 0, 180, WHITE, w=0.016)

@scene("crown")
def _(c, t):
    y = 0.56 - abs(math.sin(t * math.pi)) * 0.04
    c.poly([(0.2, y + 0.16), (0.8, y + 0.16), (0.8, y - 0.02), (0.66, y + 0.06), (0.5, y - 0.14),
            (0.34, y + 0.06), (0.2, y - 0.02)], fill=AMBER)
    c.rect(0.2, y + 0.16, 0.8, y + 0.24, fill=mix(AMBER, BROWN, 0.3), r=0.02)
    for i, x in enumerate([0.32, 0.5, 0.68]):
        c.circle(x, y + 0.2, 0.028, fill=[RED, CYAN, GREEN][i])
    sparkle(c, 0.5, y - 0.2, 0.05, fade(WHITE, 0.4 + 0.6 * math.sin(t * TAU)))

@scene("ghost")
def _(c, t):
    y = 0.46 + math.sin(t * TAU) * 0.05
    c.circle(0.5, y, 0.24, fill=WHITE)
    c.rect(0.26, y, 0.74, y + 0.26, fill=WHITE)
    for k in range(4):
        x = 0.32 + k * 0.12
        c.circle(x, y + 0.26 + math.sin(t * TAU + k) * 0.015, 0.06, fill=WHITE)
    c.circle(0.42, y - 0.04, 0.04, fill=DARK)
    c.circle(0.58, y - 0.04, 0.04, fill=DARK)
    c.ellipse(0.5, y + 0.1, 0.05, 0.035, fill=DARK)

@scene("bomb")
def _(c, t):
    c.circle(0.46, 0.62, 0.26, fill=DARK)
    c.circle(0.38, 0.54, 0.06, fill=fade(WHITE, 0.3))
    c.rect(0.56, 0.3, 0.64, 0.42, fill=SLATE, r=0.02)
    fl = 1 - t
    pts = [(0.6 + math.sin(j) * 0.03, 0.3 - j * 0.05 * fl) for j in range(4)]
    c.line(pts, fill=WHITE, w=0.012)
    fx, fy = pts[-1]
    for k in range(6):
        a = k * TAU / 6 + t * 6
        c.circle(fx + 0.035 * math.cos(a), fy + 0.035 * math.sin(a), 0.018, fill=AMBER if k % 2 else RED)

@scene("target lock")
def _(c, t):
    a = t * TAU
    c.circle(0.5, 0.5, 0.34, outline=GREEN, w=0.012)
    for k in range(4):
        aa = a + k * TAU / 4
        pts = rot([(0.5 + 0.26, 0.5 - 0.1), (0.5 + 0.38, 0.5 - 0.1), (0.5 + 0.38, 0.5 + 0.1), (0.5 + 0.26, 0.5 + 0.1)],
                  0.5, 0.5, aa)
        c.poly(pts, fill=fade(GREEN, 0.8))
    r = 0.14 + 0.03 * math.sin(t * TAU * 2)
    c.circle(0.5, 0.5, r, outline=RED, w=0.02)
    c.line([(0.5 - 0.2, 0.5), (0.5 + 0.2, 0.5)], fill=fade(GREEN, 0.5), w=0.006)
    c.line([(0.5, 0.5 - 0.2), (0.5, 0.5 + 0.2)], fill=fade(GREEN, 0.5), w=0.006)


# ================================================================== RENDER
def render(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    index, total = [], 0
    seen = set()
    for tag, fn in SCENES:
        assert tag not in seen, f"duplicate tag: {tag}"
        seen.add(tag)
        frames = []
        for k in range(FRAMES):
            c = C()
            fn(c, k / FRAMES)
            frames.append(c.out().convert("P", palette=Image.ADAPTIVE, colors=COLORS, dither=Image.NONE))
        name = tag.replace(" ", "-") + ".gif"
        path = os.path.join(out_dir, name)
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=MS, loop=0, optimize=True)
        size = os.path.getsize(path)
        total += size
        index.append({"file": name, "tag": tag})
    with open(os.path.join(out_dir, "index.json"), "w") as f:
        json.dump(index, f, indent=0)
    print(f"{len(index)} GIFs, {total/1048576:.1f} MB total, {total//len(index)//1024} KB average")
    return index


def patch_app(html_path, index):
    """Inline the pack listing into index.html so the app needs no fetch()
    to find its own GIFs — fetch() is blocked on file:// in some browsers."""
    with open(html_path) as f:
        src = f.read()
    start, end = "/* PACK:start */", "/* PACK:end */"
    i, j = src.index(start), src.index(end)
    body = ",".join('{f:"%s",t:"%s"}' % (r["file"], r["tag"]) for r in index)
    block = start + "\nconst PACK = [" + body + "];\n"
    with open(html_path, "w") as f:
        f.write(src[:i] + block + src[j:])
    print(f"inlined {len(index)} entries into {os.path.basename(html_path)}")


def stale(out_dir, index):
    """Remove GIFs from a previous run whose scene has been renamed or cut."""
    keep = {r["file"] for r in index} | {"index.json"}
    for name in sorted(os.listdir(out_dir)):
        if name not in keep:
            os.remove(os.path.join(out_dir, name))
            print("removed stale", name)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "..", "gifs")
    idx = render(out)
    stale(out, idx)
    patch_app(os.path.join(here, "..", "index.html"), idx)
