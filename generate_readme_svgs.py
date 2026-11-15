#!/usr/bin/env python3
"""Build the custom SVGs for the GitHub profile README.

    python generate_readme_svgs.py            # refresh GitHub data, then build
    python generate_readme_svgs.py --offline  # build from assets/data/github.json

Makes three images, each in a dark and a light version (GitHub picks one from the
visitor's theme), in the brand's red-on-black style with the Anton / Plus Jakarta
Sans fonts embedded:

    assets/banner-*.svg    the header
    assets/about-*.svg     the About me highlight cards
    assets/activity-*.svg  weekly contribution chart for the last 12 months
    assets/collabs-*.svg   scrolling strip of brand collaboration logos
    assets/stack-*.svg     scrolling strip of the tech stack logos
    assets/footer-*.svg    the footer: the halftone KASIF wordmark

Needs fonttools + brotli (to measure text in the woff2 fonts) and Pillow (logo sizes).
"""

import base64
import html
import json
import math
import os
import re
import sys
import urllib.request
from datetime import date, timedelta

from fontTools.ttLib import TTFont
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "assets", "src")
OUT = os.path.join(ROOT, "assets")
DATA = os.path.join(ROOT, "assets", "data", "github.json")
USER = "MdKasif0"
UA = "Mozilla/5.0 (compatible; readme-svg-generator)"
W = 1280
PAD = 64

CONTENT = {
    "name": "MD KASIF UDDIN",
    "roles": "AI SOFTWARE ENGINEER  ·  BACKEND ARCHITECT  ·  TECH CREATOR",
    "tagline": "I build LLM products and the backends behind them.",
    "stats": [("3+", "years building"), ("10+", "projects shipped"), ("20+", "brand collabs"), ("6.5K+", "followers on X")],
    "brands": ["hellyeah", "moonshot", "tinyfish", "tavus", "agentmail", "contextdev", "yapper", "molted", "fishaudio", "treg",
               "superapp", "dailydev", "agentid", "shift", "blackbox", "kimi", "unfair", "releasestack", "madeforcollab", "hopper"],
}

# ───────────────────────────── themes (brand tokens) ─────────────────────────────

THEMES = {
    "dark": {
        "bg": "#05050A", "surface": "#0B0B12", "surface2": "#111119", "text": "#F5F5F5", "text2": "#C4C3CC",
        "muted": "#8C8C9A", "line": "rgba(255,255,255,.08)", "line2": "rgba(255,255,255,.16)",
        "red": "#E5322D", "red2": "#F2503E", "glow": "229,50,45", "glowA": .2, "green": "#69D29A",
        "noise": .045, "nav": "rgba(11,11,18,.78)", "chip": "rgba(11,11,18,.82)",
        "gh": ["rgba(255,255,255,.055)", "#5C1A18", "#982320", "#D92B26", "#FF6A5B"],
        "word": ["#E5322D", "#A32025", "rgba(61,14,24,.76)", "rgba(5,5,10,0)"], "invert": False,
    },
    "light": {
        "bg": "#EEEBE5", "surface": "#E6E3DE", "surface2": "#F6F4F0", "text": "#1C1B20", "text2": "#434245",
        "muted": "#787677", "line": "rgba(21,20,26,.1)", "line2": "rgba(21,20,26,.18)",
        "red": "#E3211C", "red2": "#F13E2A", "glow": "229,50,45", "glowA": .13, "green": "#13865A",
        "noise": .06, "nav": "rgba(246,244,240,.8)", "chip": "rgba(246,244,240,.88)",
        "gh": ["rgba(21,20,26,.074)", "#E0ACAA", "#E9786F", "#E3211C", "#FF5443"],
        "word": ["#E5322D", "#E5544F", "rgba(229,50,45,.32)", "rgba(238,235,229,0)"], "invert": True,
    },
}

# ───────────────────────────── fonts: embedding and measuring ─────────────────────────────

FONT_FILES = {"an": ("Anton", "anton.woff2", "400"), "jk": ("Jakarta", "jakarta.woff2", "200 800"), "cv": ("Caveat", "caveat.woff2", "400 700")}


class Metrics:
    def __init__(self, path):
        font = TTFont(path)
        self.cmap = font.getBestCmap()
        self.hmtx = font["hmtx"].metrics
        self.upem = font["head"].unitsPerEm
        self.space = self.hmtx[self.cmap[32]][0]
        self.cap = getattr(font["OS/2"], "sCapHeight", 0) / self.upem or 0.72

    def width(self, text, size, ls=0.0, bold=1.0):
        units = sum(self.hmtx[self.cmap[ord(c)]][0] if ord(c) in self.cmap else self.space for c in text)
        return units * size / self.upem * bold + ls * max(len(text) - 1, 0)


M = {key: Metrics(os.path.join(SRC, "fonts", file)) for key, (_, file, _) in FONT_FILES.items()}
BOLD = {400: 1.0, 500: 1.02, 600: 1.045, 700: 1.07, 800: 1.09}


def wrap(text, size, max_w, weight=400, fam="jk"):
    lines, line = [], ""
    for word in text.split():
        test = f"{line} {word}".strip()
        if M[fam].width(test, size, bold=BOLD.get(weight, 1)) <= max_w or not line:
            line = test
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


_cache = {}


def asset(rel, mime):
    if rel not in _cache:
        with open(os.path.join(SRC, rel), "rb") as f:
            _cache[rel] = f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"
    return _cache[rel]


def font_css(families):
    rules = []
    for key in sorted(families):
        name, file, weight = FONT_FILES[key]
        rules.append(f"@font-face{{font-family:{name};src:url({asset('fonts/' + file, 'font/woff2')}) format('woff2');font-weight:{weight};}}")
    return "".join(rules)


# ───────────────────────────── svg building blocks ─────────────────────────────

def esc(s):
    return html.escape(str(s), quote=True)


class Doc:
    """Collects the body of one SVG plus the fonts it uses."""
    w = W
    radius = 22

    def __init__(self, t, height=None):
        self.t = t
        self.parts = []
        self.fonts = set()
        self.defs = []
        self.css = []
        self.h = height
        self.ids = 0

    def uid(self, prefix):
        self.ids += 1
        return f"{prefix}{self.ids}"

    def add(self, *s):
        self.parts.extend(s)

    def text(self, x, y, s, size, fill, fam="jk", weight=400, ls=0, anchor=None, opacity=None, italic=False):
        self.fonts.add(fam)
        attrs = [f'x="{x:.1f}"', f'y="{y:.1f}"', f'font-size="{size}"', f'fill="{fill}"', f'class="{fam}"']
        if weight != 400:
            attrs.append(f'font-weight="{weight}"')
        if ls:
            attrs.append(f'letter-spacing="{ls:.2f}"')
        if anchor:
            attrs.append(f'text-anchor="{anchor}"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        if italic:
            attrs.append('font-style="italic"')
        return f"<text {' '.join(attrs)}>{esc(s)}</text>"

    def render(self, title, desc=""):
        t, h = self.t, self.h
        clip, noise = self.uid("clip"), self.uid("noise")
        css = (
            font_css(self.fonts)
            + ".an{font-family:Anton,Impact,'Arial Narrow',sans-serif}"
            + ".jk{font-family:Jakarta,'Plus Jakarta Sans','Segoe UI',Helvetica,Arial,sans-serif}"
            + ".cv{font-family:Caveat,'Segoe Script',cursive}"
            + ".a{animation:arrive .9s cubic-bezier(.2,.7,.2,1) both}"
            + "@keyframes arrive{from{opacity:0;transform:translateY(26px)}to{opacity:1;transform:none}}"
            + ".fade{animation:fade 1.2s ease both}@keyframes fade{from{opacity:0}}"
            + ".pulse{animation:pulse 2s ease-in-out infinite}@keyframes pulse{50%{opacity:.35}}"
            + ".ring{transform-box:fill-box;transform-origin:center;animation:ring 2s ease-out infinite}"
            + "@keyframes ring{from{transform:scale(1);opacity:.6}to{transform:scale(3.2);opacity:0}}"
            + "".join(self.css)
            + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{h}" viewBox="0 0 {self.w} {h}" role="img" aria-labelledby="t d">'
            f'<title id="t">{esc(title)}</title><desc id="d">{esc(desc or title)}</desc>'
            f"<defs><style>{css}</style>"
            f'<clipPath id="{clip}"><rect width="{self.w}" height="{h}" rx="{self.radius}"/></clipPath>'
            f'<filter id="{noise}" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".82" numOctaves="3" stitchTiles="stitch"/>'
            f'<feColorMatrix type="saturate" values="0"/></filter>'
            f"{''.join(self.defs)}</defs>"
            f'<g clip-path="url(#{clip})"><rect width="{self.w}" height="{h}" fill="{t["bg"]}"/>'
            f"{''.join(self.parts)}"
            f'<rect width="{self.w}" height="{h}" filter="url(#{noise})" opacity="{t["noise"]}"/></g>'
            f'<rect x=".5" y=".5" width="{self.w - 1}" height="{h - 1}" rx="{self.radius}" fill="none" stroke="{t["line"]}"/>'
            f"</svg>"
        )


def arrow(x, y, s, color, width=1.6):
    """The site's ↗ arrow, drawn so it doesn't depend on a font glyph."""
    return (f'<path d="M{x:.1f} {y + s:.1f}L{x + s:.1f} {y:.1f}M{x + s * .3:.1f} {y:.1f}H{x + s:.1f}V{y + s * .7:.1f}" '
            f'fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')


def glow(doc, cx, cy, rx, ry, alpha=None):
    t = doc.t
    gid = doc.uid("glow")
    a = t["glowA"] if alpha is None else alpha
    doc.defs.append(f'<radialGradient id="{gid}"><stop offset="0" stop-color="rgb({t["glow"]})" stop-opacity="{a}"/>'
                    f'<stop offset="1" stop-color="rgb({t["glow"]})" stop-opacity="0"/></radialGradient>')
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#{gid})"/>'


def eyebrow(doc, x, y, label, number=None, delay=0.0):
    """'01 / SELECTED WORK ——' with the number and rule in red."""
    t = doc.t
    size, ls = 13, 2.6
    out, cx = [], x
    if number:
        out.append(doc.text(cx, y, number, size, t["red2"], weight=700, ls=ls))
        cx += M["jk"].width(number, size, ls, 1.07) + ls + 8
        out.append(doc.text(cx, y, "/", size, t["muted"], weight=700))
        cx += 16
    out.append(doc.text(cx, y, label, size, t["muted"], weight=700, ls=ls))
    cx += M["jk"].width(label, size, ls, 1.07) + 18
    out.append(f'<rect x="{cx:.1f}" y="{y - 5}" width="46" height="1.5" fill="{t["red"]}"/>')
    return f'<g class="a" style="animation-delay:{delay}s">{"".join(out)}</g>'


def title_dot(doc, x, y, text, size, ls=None):
    """The portfolio's round red full stop after a display title."""
    ls = -0.035 * size if ls is None else ls
    end = x + M["an"].width(text, size, ls) + ls  # SVG adds the spacing after the last letter too
    r = 0.0425 * size
    return f'<circle cx="{end + 0.03 * size + r:.1f}" cy="{y - r:.1f}" r="{r:.1f}" fill="{doc.t["red"]}"/>'


def display(doc, x, y, lines, size, gap=None, delay=0.1, dot=True):
    """Stacked Anton headline. lines: [(text, colour_key)]. Returns svg and the last baseline."""
    gap = gap or size * 0.9
    out = []
    for i, (txt, key) in enumerate(lines):
        yy = y + i * gap
        line = doc.text(x, yy, txt, size, doc.t[key], fam="an", ls=-0.035 * size)
        if dot and i == len(lines) - 1:
            line += title_dot(doc, x, yy, txt, size)
        out.append(f'<g class="a" style="animation-delay:{delay + i * .12:.2f}s">{line}</g>')
    return "".join(out), y + (len(lines) - 1) * gap


def pill(doc, x, y, label, size=12, fill=None, stroke=None, color=None, weight=700, ls=1.6, padx=12, h=28):
    t = doc.t
    w = M["jk"].width(label, size, ls, BOLD[weight]) + padx * 2
    parts = [f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{fill or "none"}"'
             + (f' stroke="{stroke}"' if stroke else "") + "/>",
             doc.text(x + padx, y + h / 2 + size * .36, label, size, color or t["text"], weight=weight, ls=ls)]
    return "".join(parts), w


def pulse_dot(doc, cx, cy, color, r=4):
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" class="ring"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" class="pulse"/>')




# ───────────────────────────── brand logo strip ─────────────────────────────

def collabs(t):
    d = Doc(t, 360)
    d.fonts |= {"an", "jk"}
    d.add(glow(d, 200, 360, 500, 200, t["glowA"] * .7))
    d.add(f'<g class="a">{d.text(PAD, 70, "BEEN PART OF /", 13, t["muted"], weight=700, ls=2.6)}</g>',
          f'<g class="a" style="animation-delay:.1s">{d.text(PAD - 2, 136, "THE BIGGER PICTURE", 64, t["text"], fam="an", ls=-2.2)}'
          f'{title_dot(d, PAD - 2, 136, "THE BIGGER PICTURE", 64, -2.2)}</g>',
          f'<g class="a" style="animation-delay:.2s">{d.text(W - PAD - 150, 130, "20+", 64, t["red"], fam="an", anchor="end")}'
          f'{d.text(W - PAD - 136, 108, "brand", 15, t["text2"])}{d.text(W - PAD - 136, 130, "collaborations", 15, t["text2"])}</g>')
    inv, edge = d.uid("inv"), d.uid("edge")
    d.defs.append(f'<filter id="{inv}"><feColorMatrix type="matrix" values="-1 0 0 0 1 0 -1 0 0 1 0 0 -1 0 1 0 0 0 1 0"/>'
                  f'<feColorMatrix type="hueRotate" values="180"/></filter>'
                  f'<linearGradient id="{edge}g"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".08" stop-color="#fff"/>'
                  f'<stop offset=".92" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                  f'<mask id="{edge}"><rect width="{W}" height="360" fill="url(#{edge}g)"/></mask>')
    brands = CONTENT["brands"]
    for r, row in enumerate([brands[:10], brands[10:]]):
        cells, x = [], 0
        for b in row:
            iw, ih = Image.open(os.path.join(SRC, "brands", b + ".png")).size
            h = 30 if b == "kimi" else 26
            w = iw * h / ih
            box = w + 56
            filt = f' filter="url(#{inv})"' if t["invert"] and b != "kimi" else ""
            cells.append(f'<rect x="{x:.1f}" y="0" width="{box:.1f}" height="64" rx="14" fill="{t["surface"]}" stroke="{t["line"]}"/>'
                         f'<image href="{asset("brands/" + b + ".png", "image/png")}" x="{x + 28:.1f}" y="{32 - h / 2:.1f}" width="{w:.1f}" height="{h}"{filt} opacity=".9"/>')
            x += box + 14
        set_w = x
        name = f"mq{r}"
        frames = (f"from{{transform:translateX(0)}}to{{transform:translateX(-{set_w:.0f}px)}}" if r == 0 else
                  f"from{{transform:translateX(-{set_w:.0f}px)}}to{{transform:translateX(0)}}")
        d.css.append(f".{name}{{animation:{name} {38 + r * 6}s linear infinite}}@keyframes {name}{{{frames}}}")
        sid = d.uid("strip")
        d.defs.append(f'<g id="{sid}">{"".join(cells)}</g>')  # embedded once, drawn three times for a seamless loop
        d.add(f'<g mask="url(#{edge})"><g transform="translate(0 {178 + r * 80})"><g class="{name}">'
              + "".join(f'<use href="#{sid}" x="{k * set_w:.0f}"/>' for k in range(3)) + "</g></g></g>")
    return d.render("Been part of the bigger picture — 20+ brand collaborations",
                    "Brands: HellYeah.ai, Moonshot AI, TinyFish, Tavus, AgentMail, Context.dev, Yapper.so, Molted, Fish Audio, Treg, SuperApp, "
                    "daily.dev, AgentID, Shift, Blackbox AI, Kimi, Unfair.so, ReleaseStack, Made For Collab, Hopper.")




# ───────────────────────────── about: highlight cards ─────────────────────────────

# Simple 24×24 line icons, drawn here so they need no icon font.
ICONS = {
    "code": "M8 7l-5 5 5 5M16 7l5 5-5 5M13.5 4l-3 16",
    "trophy": "M8 4h8v5a4 4 0 0 1-8 0zM8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8.5 20h7M10 17h4",
    "cap": "M2 9l10-5 10 5-10 5zM6 11v5c3 2.5 9 2.5 12 0v-5M22 9v6",
    "signal": "M12 13.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3zM8.5 15.5a5 5 0 0 1 0-7M15.5 8.5a5 5 0 0 1 0 7M5.6 18.4a9 9 0 0 1 0-12.8M18.4 5.6a9 9 0 0 1 0 12.8",
    "briefcase": "M3 8h18v11H3zM8.5 8V5.5h7V8M3 13h18M11 12h2v2h-2z",
    "bolt": "M13 2L4.5 13.5H12L11 22l8.5-11.5H12z",
}

HIGHLIGHTS = [
    ("code", "CURRENTLY BUILDING", "GitRoasted", "Scores any GitHub profile out of 1,000, then lets an AI roast it."),
    ("trophy", "RECOGNITION", "1st Runner-Up", "InnoSprint 2.0, D4 Community × Google for Developers, with GigSense."),
    ("cap", "EDUCATION", "B.Tech CSE", "Chandigarh University, Mohali. First year, 2026 to now."),
    ("signal", "BUILDING IN PUBLIC", "6,500+ on X", "Plus 20+ collaborations with AI and dev-tool brands."),
    ("briefcase", "OPEN TO FREELANCE", "Available now", "AI product MVPs, backend and API builds, and AI features for existing apps."),
    ("bolt", "FUN FACT", "Automating myself", "I write Python so AI can replace me faster."),
]


def about(t):
    cols, gap, ch = 3, 20, 236
    cw = (W - 2 * 40 - (cols - 1) * gap) / cols
    rows = (len(HIGHLIGHTS) + cols - 1) // cols
    H = 40 + rows * ch + (rows - 1) * gap + 40
    d = Doc(t, H)
    d.fonts |= {"an", "jk"}
    d.add(glow(d, 1100, 0, 560, 260, t["glowA"] * .6), glow(d, 120, H, 520, 220, t["glowA"] * .45))
    for i, (icon, label, title, desc) in enumerate(HIGHLIGHTS):
        r, c = divmod(i, cols)
        x, y = 40 + c * (cw + gap), 40 + r * (ch + gap)
        card = [f'<rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="{ch}" rx="18" fill="{t["surface"]}" stroke="{t["line"]}"/>',
                f'<rect x="{x + 26:.1f}" y="{y}" width="56" height="2" fill="{t["red"]}"/>',
                f'<rect x="{x + 26:.1f}" y="{y + 28}" width="48" height="48" rx="13" fill="rgb({t["glow"]})" fill-opacity=".12" stroke="rgb({t["glow"]})" stroke-opacity=".35"/>',
                f'<g transform="translate({x + 38:.1f} {y + 40})"><path d="{ICONS[icon]}" fill="none" stroke="{t["red2"]}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></g>',
                d.text(x + cw - 26, y + 58, f"{i + 1:02d}", 13, t["muted"], weight=700, ls=1.5, anchor="end"),
                d.text(x + 26, y + 112, label, 11.5, t["red2"], weight=700, ls=2.2),
                d.text(x + 24, y + 152, title.upper(), 34, t["text"], fam="an", ls=-.4)]
        for j, line in enumerate(wrap(desc, 15, cw - 52)[:3]):
            card.append(d.text(x + 26, y + 184 + j * 22, line, 15, t["text2"]))
        d.add(f'<g class="a" style="animation-delay:{.1 + i * .08:.2f}s">{"".join(card)}</g>')
    return d.render("About me — highlights",
                    " ".join(f"{label.title()}: {title}. {desc}" for _, label, title, desc in HIGHLIGHTS))


# ───────────────────────────── tech stack strip ─────────────────────────────

def _luminance(hex_):
    r, g, b = (int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lin = lambda c: c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
    return .2126 * lin(r) + .7152 * lin(g) + .0722 * lin(b)


def stack(t):
    """The tech stack as two rows of logo pills scrolling in opposite directions, like the collabs strip."""
    with open(os.path.join(SRC, "tech.json")) as f:
        icons = json.load(f)["icons"]
    d = Doc(t, 360)
    d.fonts |= {"an", "jk"}
    d.add(glow(d, 1080, 360, 500, 200, t["glowA"] * .7))
    count = str(len(icons))
    d.add(f'<g class="a">{d.text(PAD, 70, "WHAT I SHIP WITH /", 13, t["muted"], weight=700, ls=2.6)}</g>',
          f'<g class="a" style="animation-delay:.1s">{d.text(PAD - 2, 136, "THE STACK", 64, t["text"], fam="an", ls=-2.2)}'
          f'{title_dot(d, PAD - 2, 136, "THE STACK", 64, -2.2)}</g>',
          f'<g class="a" style="animation-delay:.2s">{d.text(W - PAD - 150, 130, count, 64, t["red"], fam="an", anchor="end")}'
          f'{d.text(W - PAD - 136, 108, "tools in", 15, t["text2"])}{d.text(W - PAD - 136, 130, "daily use", 15, t["text2"])}</g>')
    edge = d.uid("edge")
    d.defs.append(f'<linearGradient id="{edge}g"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".08" stop-color="#fff"/>'
                  f'<stop offset=".92" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                  f'<mask id="{edge}"><rect width="{W}" height="360" fill="url(#{edge}g)"/></mask>')
    tile = "#16161E"  # every logo sits on the same dark tile, so brand colours read in both themes
    half = (len(icons) + 1) // 2
    for r, row in enumerate([icons[:half], icons[half:]]):
        cells, x = [], 0
        for ic in row:
            color = ic["color"] if _luminance(ic["color"]) > .06 else "#F5F5F5"  # black or near-black marks go white
            label_w = M["jk"].width(ic["name"], 16, bold=1.045)
            box = 12 + 40 + 14 + label_w + 24
            rule = ' fill-rule="evenodd"' if ic["evenodd"] else ""
            cells.append(f'<rect x="{x:.1f}" y="0" width="{box:.1f}" height="64" rx="14" fill="{t["surface"]}" stroke="{t["line"]}"/>'
                         f'<rect x="{x + 12:.1f}" y="12" width="40" height="40" rx="10" fill="{tile}"/>'
                         f'<svg x="{x + 20:.1f}" y="20" width="24" height="24" viewBox="{ic["viewBox"]}"><path d="{ic["d"]}" fill="{color}"{rule}/></svg>'
                         + d.text(x + 66, 37.5, ic["name"], 16, t["text"], weight=600))
            x += box + 14
        set_w = x
        name = f"st{r}"
        frames = (f"from{{transform:translateX(0)}}to{{transform:translateX(-{set_w:.0f}px)}}" if r == 0 else
                  f"from{{transform:translateX(-{set_w:.0f}px)}}to{{transform:translateX(0)}}")
        d.css.append(f".{name}{{animation:{name} {38 + r * 6}s linear infinite}}@keyframes {name}{{{frames}}}")
        sid = d.uid("srow")
        d.defs.append(f'<g id="{sid}">{"".join(cells)}</g>')
        d.add(f'<g mask="url(#{edge})"><g transform="translate(0 {178 + r * 80})"><g class="{name}">'
              + "".join(f'<use href="#{sid}" x="{k * set_w:.0f}"/>' for k in range(3)) + "</g></g></g>")
    return d.render(f"The stack — {len(icons)} tools in daily use", ", ".join(i["name"] for i in icons) + ".")


# ───────────────────────────── GitHub data ─────────────────────────────

def fetch_github():
    """Port of the portfolio's tools/github/fetch.mjs."""
    def get(url, headers=None):
        req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
        token = os.environ.get("GITHUB_TOKEN")
        if token and url.startswith("https://api.github.com/"):
            req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode()

    page = get(f"https://github.com/users/{USER}/contributions", {"X-Requested-With": "XMLHttpRequest"})
    counts = {}
    for cid, txt in re.findall(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>([^<]+)</tool-tip>', page):
        m = re.match(r"^(\d[\d,]*)", txt)
        counts[cid] = 0 if txt.startswith("No ") or not m else int(m.group(1).replace(",", ""))
    days = []
    for tag, day in re.findall(r'(<td\b[^>]*\bdata-date="(\d{4}-\d\d-\d\d)"[^>]*>)', page):
        lvl = re.search(r'data-level="(\d)"', tag)
        cid = re.search(r'\bid="([^"]+)"', tag)
        days.append((day, int(lvl.group(1)) if lvl else 0, counts.get(cid.group(1) if cid else "", 0)))
    days.sort()
    total = re.search(r"([\d,]+)\s+contributions?\s+in the last year", page)
    if len(days) < 300 or not total:
        raise RuntimeError(f"unexpected contributions page ({len(days)} days)")
    repos = json.loads(get(f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed", {"Accept": "application/vnd.github+json"}))
    own = [r for r in repos if not r["fork"]]
    data = {"user": USER, "asOf": date.today().isoformat(), "contributions": int(total.group(1).replace(",", "")),
            "start": days[0][0], "levels": "".join(str(l) for _, l, _ in days), "counts": [c for _, _, c in days],
            "repos": len(own), "stars": sum(r["stargazers_count"] for r in own),
            "lastPush": {"repo": own[0]["name"], "at": own[0]["pushed_at"]} if own else None}
    with open(DATA, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    return data


def streaks(counts):
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    i = len(counts) - 1
    if i >= 0 and counts[i] == 0:
        i -= 1  # today may not have a commit yet
    current = 0
    while i >= 0 and counts[i]:
        current += 1
        i -= 1
    return current, longest



# ───────────────────────────── header banner ─────────────────────────────

def banner(t):
    d = Doc(t, 420)
    c = CONTENT
    d.fonts |= {"an", "jk"}
    # faint grid that fades out from the top left, plus the red glow behind the avatar
    gid, gm = d.uid("grid"), d.uid("gridmask")
    d.defs.append(f'<pattern id="{gid}" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="{t["text"]}" stroke-opacity=".06"/></pattern>'
                  f'<radialGradient id="{gm}g" cx=".25" cy=".2" r=".9"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
                  f'<mask id="{gm}"><rect width="{W}" height="420" fill="url(#{gm}g)"/></mask>')
    d.add(f'<rect width="{W}" height="420" fill="url(#{gid})" mask="url(#{gm})"/>',
          glow(d, 1060, 230, 360, 300, t["glowA"] * 1.2), glow(d, 120, 420, 420, 160, t["glowA"] * .5))

    # nav bar, the same as the portfolio's: logo mark, KASIF., section links, theme button, "Let's talk"
    nav = [f'<rect x="24" y="18" width="{W - 48}" height="56" rx="28" fill="{t["nav"]}" stroke="{t["line"]}"/>',
           '<clipPath id="lm"><rect x="38" y="28" width="36" height="36" rx="18"/></clipPath>',
           f'<image href="{asset("logo-mark.png", "image/png")}" x="38" y="28" width="36" height="36" clip-path="url(#lm)"/>',
           d.text(84, 56, "KASIF", 25, t["text"], fam="an", ls=-.4), title_dot(d, 84, 56, "KASIF", 25, -.4)]
    links = ["Work", "Recognition", "About", "Journey", "Services", "Contact"]
    widths = [M["jk"].width(l, 14, bold=1.02) for l in links]
    lx = W / 2 - (sum(widths) + 38 * (len(links) - 1)) / 2
    for i, (l, lw) in enumerate(zip(links, widths)):
        nav.append(d.text(lx, 51, l, 14, t["text"] if i == 0 else t["muted"], weight=500))
        if i == 0:
            nav.append(f'<rect x="{lx:.1f}" y="59" width="{lw:.1f}" height="1.5" fill="{t["red"]}"/>')
        lx += lw + 38
    talk, tw = pill(d, 0, 0, "Let's talk", 14, stroke=t["line2"], weight=600, ls=0, padx=18, h=34)
    tx = W - 40 - tw - 14
    nav.append(f'<g transform="translate({tx:.1f} 29)">{talk}{arrow(tw - 6, 11, 9, t["red2"])}</g>')
    # theme button: a crescent moon in a ring, like the portfolio's toggle
    mx = tx - 30
    nav.append(f'<circle cx="{mx:.1f}" cy="46" r="17" fill="none" stroke="{t["line2"]}"/>'
               f'<path d="M{mx + 4:.1f} 40.5a6.5 6.5 0 1 0 2.6 9.6 5.2 5.2 0 0 1-2.6-9.6z" fill="none" stroke="{t["text"]}" stroke-width="1.4" stroke-linejoin="round"/>')
    d.add(f'<g class="fade">{"".join(nav)}</g>')

    # name, roles, typed tagline
    d.add(f'<g class="a" style="animation-delay:.1s">{d.text(PAD, 128, "HEY THERE, I’M", 13, t["muted"], weight=700, ls=3)}</g>',
          f'<g class="a" style="animation-delay:.2s">{d.text(PAD - 4, 224, c["name"], 100, t["text"], fam="an", ls=-2)}'
          f'{title_dot(d, PAD - 4, 224, c["name"], 100, -2)}</g>',
          f'<g class="a" style="animation-delay:.35s">{d.text(PAD, 262, c["roles"], 15, t["red2"], weight=700, ls=2.2)}</g>')
    ty = 304
    tw = M["jk"].width(c["tagline"], 19, bold=1.02)
    clip = d.uid("type")
    dur = 2.6
    # typing: hidden for the first 0.9s, then one letter-ish step at a time. The rect's own width is the
    # full line, so a viewer without SMIL still sees the whole tagline.
    lead = 0.9 / (0.9 + dur)
    widths = ["0"] + [f"{tw * i / 48 + (4 if i == 48 else 0):.0f}" for i in range(49)]
    times = ["0"] + [f"{lead + (1 - lead) * i / 48:.4f}" for i in range(49)]
    d.defs.append(f'<clipPath id="{clip}"><rect x="{PAD + 22}" y="{ty - 22}" height="30" width="{tw + 4:.0f}">'
                  f'<animate attributeName="width" begin="0s" dur="{0.9 + dur}s" fill="freeze" calcMode="discrete" '
                  f'values="{";".join(widths)}" keyTimes="{";".join(times)}"/></rect></clipPath>')
    d.add(f'<g class="a" style="animation-delay:.5s">{d.text(PAD, ty, ">", 19, t["red2"], weight=700)}</g>',
          f'<g clip-path="url(#{clip})">{d.text(PAD + 22, ty, c["tagline"], 19, t["text"], weight=500)}</g>',
          f'<rect x="{PAD + 28 + tw:.0f}" y="{ty - 17}" width="10" height="21" fill="{t["red2"]}">'
          f'<animate attributeName="x" values="{";".join([str(PAD + 24)] + [f"{PAD + 24 + tw * i / 48 + (4 if i == 48 else 0):.0f}" for i in range(49)])}" '
          f'keyTimes="{";".join(times)}" calcMode="discrete" begin="0s" dur="{0.9 + dur}s" fill="freeze"/>'
          f'<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/></rect>')

    # stat chips
    x = PAD
    chips = []
    for v, label in c["stats"]:
        vw = M["an"].width(v, 22)
        lw = M["jk"].width(label, 13, bold=1.02)
        w = vw + lw + 44
        chips.append(f'<rect x="{x:.1f}" y="334" width="{w:.1f}" height="42" rx="21" fill="{t["chip"]}" stroke="{t["line2"]}"/>'
                     + d.text(x + 18, 363, v, 22, t["red"], fam="an")
                     + d.text(x + 26 + vw, 360, label, 13, t["text2"], weight=500))
        x += w + 10
    d.add(f'<g class="a" style="animation-delay:.7s">{"".join(chips)}</g>')

    # avatar in a ring, with a slowly turning dashed orbit
    cx, cy, r = 1060, 232, 128
    ac = d.uid("av")
    d.defs.append(f'<clipPath id="{ac}"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>')
    d.css.append(".spin{transform-box:view-box;transform-origin:1060px 232px;animation:spin 40s linear infinite}"
                 ".spin2{transform-box:view-box;transform-origin:1060px 232px;animation:spin 12s linear infinite reverse}"
                 "@keyframes spin{to{transform:rotate(360deg)}}")
    d.add(f'<g class="fade" style="animation-delay:.2s">'
          f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{t["surface"]}"/>'
          f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="rgb({t["glow"]})" fill-opacity="{t["glowA"] * .9}"/>'
          f'<image href="{asset("avatar.webp", "image/webp")}" x="{cx - r * 1.12:.0f}" y="{cy - r * .8:.0f}" width="{r * 2.24:.0f}" height="{r * 2.24:.0f}" clip-path="url(#{ac})"/>'
          f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{t["red"]}" stroke-width="2"/>'
          f'<g class="spin"><circle cx="{cx}" cy="{cy}" r="{r + 18}" fill="none" stroke="{t["red"]}" stroke-opacity=".45" stroke-dasharray="2 10" stroke-linecap="round"/></g>'
          f'<g class="spin2"><circle cx="{cx}" cy="{cy - r - 18}" r="5" fill="{t["red2"]}"/></g>'
          f'</g>')
    tag, tw2 = pill(d, 0, 0, "INDIA", 11, ls=2, h=28)
    d.add(f'<g class="a" style="animation-delay:.9s"><g transform="translate({cx - tw2 / 2:.0f} {cy + r - 6})">'
          + tag.replace('fill="none"', f'fill="{t["chip"]}" stroke="{t["line2"]}"', 1) + "</g></g>")
    return d.render("Md Kasif Uddin — AI Software Engineer, Backend Architect, Tech Creator",
                    "Hey there, I'm Md Kasif Uddin from India. I build LLM products and the backends behind them. "
                    "3+ years building, 10+ projects shipped, 20+ brand collaborations, 6.5K+ followers on X. Open to work.")


# ───────────────────────────── contribution activity chart ─────────────────────────────

def smooth(points):
    """Catmull-Rom through the points, as cubic Béziers."""
    out = [f"M{points[0][0]:.1f} {points[0][1]:.1f}"]
    for i in range(len(points) - 1):
        p0 = points[max(i - 1, 0)]
        p1, p2 = points[i], points[i + 1]
        p3 = points[min(i + 2, len(points) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        out.append(f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}")
    return "".join(out)


def activity(t, gh):
    d = Doc(t, 560)
    d.fonts |= {"an", "jk"}
    start = date.fromisoformat(gh["start"])
    counts = gh["counts"]
    # weekly totals, weeks starting on Sunday like GitHub's graph
    first = (start.weekday() + 1) % 7
    weeks = {}
    for i, n in enumerate(counts):
        wk = (i + first) // 7
        weeks.setdefault(wk, [start + timedelta(days=i - (i + first) % 7), 0])[1] += n
    series = [weeks[k] for k in sorted(weeks)]
    total = gh["contributions"]
    peak_i = max(range(len(series)), key=lambda i: series[i][1])
    top = max(10, series[peak_i][1])
    # a round axis: four gridline steps of a round number
    raw = top * 1.12 / 4
    mag = 10 ** math.floor(math.log10(raw))
    tick = next(m * mag for m in (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10) if m * mag >= raw)
    ymax = tick * 4

    d.add(glow(d, 1000, 120, 520, 240, t["glowA"] * .7))
    d.add(f'<g class="a">{d.text(PAD, 66, "CONTRIBUTION ACTIVITY", 13, t["red2"], weight=700, ls=2.6)}'
          f'{d.text(PAD + M["jk"].width("CONTRIBUTION ACTIVITY", 13, 2.6, 1.07) + 14, 66, "· LAST 12 MONTHS, PER WEEK", 13, t["muted"], weight=700, ls=2.6)}</g>')
    num = f"{total:,}"
    d.add(f'<g class="a" style="animation-delay:.1s">{d.text(PAD - 2, 140, num, 64, t["text"], fam="an")}'
          f'{d.text(PAD + M["an"].width(num, 64) + 12, 138, "contributions", 22, t["text2"], weight=500)}</g>')
    as_of = date.fromisoformat(gh["asOf"])
    updated = f"UPDATED {as_of.day} {as_of.strftime('%b %Y').upper()}"
    d.add(f'<g class="fade">{d.text(W - PAD, 66, updated, 11, t["muted"], weight=700, ls=1.6, anchor="end")}</g>')

    x0, x1, y0, y1 = PAD + 40, W - PAD, 196, 400
    sx = lambda i: x0 + (x1 - x0) * i / (len(series) - 1)
    sy = lambda v: y1 - (y1 - y0) * v / ymax
    grid = []
    for k in range(5):
        v = ymax * k / 4
        y = sy(v)
        grid.append(f'<rect x="{x0}" y="{y:.1f}" width="{x1 - x0}" height="1" fill="{t["line"] if k else t["line2"]}"/>')
        grid.append(d.text(x0 - 12, y + 4, f"{v:,.0f}", 11, t["muted"], weight=600, anchor="end"))
    last_month = None
    for i, (wk_start, _) in enumerate(series):
        if wk_start.month != last_month and (wk_start.day <= 7 or i == 0):
            last_month = wk_start.month
            if i:
                grid.append(d.text(sx(i), y1 + 26, wk_start.strftime("%b"), 11, t["muted"], weight=600, anchor="middle"))
    d.add(f'<g class="fade">{"".join(grid)}</g>')

    pts = [(sx(i), sy(v)) for i, (_, v) in enumerate(series)]
    line = smooth(pts)
    ag = d.uid("area")
    d.defs.append(f'<linearGradient id="{ag}" x1="0" y1="{y0}" x2="0" y2="{y1}" gradientUnits="userSpaceOnUse">'
                  f'<stop offset="0" stop-color="{t["red"]}" stop-opacity=".45"/><stop offset="1" stop-color="{t["red"]}" stop-opacity="0"/></linearGradient>')
    d.css.append(".line{stroke-dasharray:1;stroke-dashoffset:1;animation:line 2.4s .3s cubic-bezier(.6,0,.2,1) forwards}@keyframes line{to{stroke-dashoffset:0}}")
    d.add(f'<path d="{line}L{x1} {y1}L{x0} {y1}Z" fill="url(#{ag})" class="fade" style="animation-delay:.9s;animation-duration:1.8s"/>',
          f'<path d="{line}" pathLength="1" class="line" fill="none" stroke="{t["red2"]}" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round"/>')
    px, py = pts[peak_i]
    when = series[peak_i][0]
    label = f"Peak: {series[peak_i][1]} in the week of {when.day} {when.strftime('%b')}"
    lw = M["jk"].width(label, 12, bold=1.045) + 24
    lx = min(max(px - lw / 2, x0), x1 - lw)
    d.add(f'<g class="a" style="animation-delay:2.4s"><line x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{y0 - 16}" stroke="{t["red"]}" stroke-dasharray="3 4"/>'
          f'<circle cx="{px:.1f}" cy="{py:.1f}" r="9" fill="{t["red"]}" fill-opacity=".2"/><circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="{t["red2"]}" stroke="{t["bg"]}" stroke-width="2"/>'
          f'<rect x="{lx:.1f}" y="{y0 - 44}" width="{lw:.1f}" height="28" rx="14" fill="{t["red"]}"/>'
          f'{d.text(lx + 12, y0 - 25.5, label, 12, "#FFFFFF", weight=600)}</g>')
    lx_, ly_ = pts[-1]
    d.add(f'<g class="fade" style="animation-delay:2.6s">{pulse_dot(d, round(lx_, 1), round(ly_, 1), t["red2"], 4.5)}</g>')

    # summary row
    best = max(range(len(counts)), key=lambda i: counts[i])
    best_day = start + timedelta(days=best)
    cur, longest = streaks(counts)
    by_dow = [0] * 7
    for i, n in enumerate(counts):
        by_dow[(start + timedelta(days=i)).weekday()] += n
    busiest = ["Mondays", "Tuesdays", "Wednesdays", "Thursdays", "Fridays", "Saturdays", "Sundays"][max(range(7), key=lambda k: by_dow[k])]
    active = sum(1 for n in counts if n)
    stats = [(f"{counts[best]}", f"BEST DAY · {best_day.day} {best_day.strftime('%b').upper()}"), (f"{cur}", "CURRENT STREAK (DAYS)"),
             (f"{longest}", "LONGEST STREAK (DAYS)"), (f"{active}", "ACTIVE DAYS"), (busiest, "MOST ACTIVE ON")]
    y = 462
    sw = (W - 2 * PAD) / len(stats)
    row = [f'<rect x="{PAD}" y="{y}" width="{W - 2 * PAD}" height="1" fill="{t["line2"]}"/>']
    for i, (v, lab) in enumerate(stats):
        x = PAD + i * sw
        if i:
            row.append(f'<rect x="{x - 18:.1f}" y="{y + 20}" width="1" height="56" fill="{t["line"]}"/>')
        row.append(d.text(x, y + 56, v, 36, t["red"] if i == 0 else t["text"], fam="an"))
        row.append(d.text(x, y + 80, lab, 11, t["muted"], weight=700, ls=1.4))
    d.add(f'<g class="a" style="animation-delay:.6s">{"".join(row)}</g>')
    return d.render(f"{total:,} GitHub contributions in the last 12 months",
                    f"Weekly contributions chart. Best day: {counts[best]} on {best_day.isoformat()}. "
                    f"Current streak {cur} days, longest {longest} days, {active} active days, most active on {busiest}.")


# ───────────────────────────── footer (the portfolio's halftone KASIF wordmark) ─────────────────────────────

def footer(t):
    light = t["invert"]
    ink = "#D42A25" if light else "#E5322D"
    # the wordmark spans the width; its height sets how tall the footer is (20% of it is cropped off)
    size = 520
    ww = M["an"].width("KASIF", size, -0.055 * size)
    size = round(size * (W - 24) / ww)
    cap = size * M["an"].cap
    top = 48
    H = int(top + cap * 0.8)
    d = Doc(t, H)
    d.fonts |= {"an"}
    # hairline across the top, brightest in the middle, and the red glow rising from the bottom
    hl = d.uid("hair")
    d.defs.append(f'<linearGradient id="{hl}"><stop offset="0" stop-color="{t["text"]}" stop-opacity="0"/>'
                  f'<stop offset=".18" stop-color="{t["text"]}" stop-opacity=".12"/><stop offset=".5" stop-color="{t["red2"]}" stop-opacity=".65"/>'
                  f'<stop offset=".82" stop-color="{t["text"]}" stop-opacity=".12"/><stop offset="1" stop-color="{t["text"]}" stop-opacity="0"/></linearGradient>')
    d.add(glow(d, W / 2, H, 700, 420, .18 if not light else .12), f'<rect x="40" y="0" width="{W - 80}" height="1" fill="url(#{hl})"/>')

    # the halftone KASIF wordmark: dots masked by the letters, cropped at the bottom edge
    ls = -0.055 * size
    ww = M["an"].width("KASIF", size, ls)
    x = (W - ww) / 2
    base = top + cap
    dots, mask, grad, sweep = d.uid("dots"), d.uid("wm"), d.uid("ink"), d.uid("sweep")
    d.defs.append(f'<pattern id="{dots}" width="7" height="7" patternUnits="userSpaceOnUse"><circle cx="3.5" cy="3.5" r="2.4" fill="#fff"/></pattern>'
                  f'<mask id="{mask}"><text x="{x:.1f}" y="{base:.1f}" font-size="{size}" class="an" letter-spacing="{ls:.1f}" fill="url(#{dots})">KASIF</text></mask>'
                  f'<linearGradient id="{grad}" x1="0" y1="{top:.0f}" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">'
                  f'<stop offset="0" stop-color="{ink}"/><stop offset=".55" stop-color="{ink}" stop-opacity=".85"/>'
                  f'<stop offset="1" stop-color="{ink}" stop-opacity="{.35 if not light else .45}"/></linearGradient>'
                  f'<linearGradient id="{sweep}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                  f'<stop offset=".5" stop-color="#fff" stop-opacity="{.55 if not light else .7}"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    d.css.append(".sweep{animation:sweep 6s 1.2s ease-in-out infinite}@keyframes sweep{0%{transform:translateX(-420px)}45%,100%{transform:translateX(1700px)}}")
    d.add(f'<g class="fade" style="animation-delay:.4s;animation-duration:1.6s" mask="url(#{mask})">'
          f'<rect x="0" y="{top - 10:.0f}" width="{W}" height="{H - top + 10:.0f}" fill="url(#{grad})"/>'
          f'<g class="sweep"><rect x="0" y="{top - 10:.0f}" width="320" height="{H - top + 10:.0f}" fill="url(#{sweep})" transform="skewX(-14)"/></g></g>')
    return d.render("KASIF", "The KASIF wordmark in red halftone dots.")


# ───────────────────────────── main ─────────────────────────────

def main():
    gh = None
    if "--offline" not in sys.argv:
        try:
            gh = fetch_github()
            print(f"↻ GitHub: {gh['contributions']} contributions, {gh['repos']} repos, {gh['stars']} stars")
        except Exception as exc:  # network, rate limit or a changed page: keep the last snapshot
            print(f"⚠ GitHub fetch failed, using the saved snapshot ({exc})")
    if gh is None:
        with open(DATA) as f:
            gh = json.load(f)
    for name, theme in THEMES.items():
        files = {"banner": banner(theme), "about": about(theme), "activity": activity(theme, gh), "collabs": collabs(theme), "stack": stack(theme), "footer": footer(theme)}
        for k, svg in files.items():
            with open(os.path.join(OUT, f"{k}-{name}.svg"), "w", encoding="utf-8") as f:
                f.write(svg)
        print(f"✅ {name}: {', '.join(f'{k} {len(s) / 1024:.0f} KB' for k, s in files.items())}")


if __name__ == "__main__":
    main()
