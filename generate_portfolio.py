#!/usr/bin/env python3
"""Build the portfolio-styled SVG sections for the GitHub profile README.

Every section of kasif-portfolio.netlify.app is redrawn as an animated SVG in a dark
and a light version, using the site's own fonts (Anton, Plus Jakarta Sans, Caveat),
colours and copy. Fonts and images are embedded as data URIs because GitHub shows
SVGs as images, which can't load anything external.

    python generate_portfolio.py            # refresh GitHub data, then build
    python generate_portfolio.py --offline  # build from assets/data/github.json

Needs fonttools + brotli (to measure text in the woff2 fonts) and Pillow (logo sizes).
Copy lives in CONTENT below; update it when the portfolio's data/content.ts changes.
Contact links (email and so on) live in README.md, not in the images.
"""

import base64
import html
import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime, timedelta

from fontTools.ttLib import TTFont
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "assets", "src")
OUT = os.path.join(ROOT, "assets")
DATA = os.path.join(ROOT, "assets", "data", "github.json")
USER = "MdKasif0"
UA = "Mozilla/5.0 (compatible; readme-svg-generator)"
W = 1280          # every full-width section shares this width so they scale together
PAD = 64          # page gutter inside a section

# ───────────────────────────── content (mirrors the portfolio's data/content.ts) ─────────────────────────────

CONTENT = {
    "hero": {
        "eyebrow": "AI ENGINEER / BACKEND ARCHITECT / TECH CREATOR",
        "availability": "OPEN TO WORK · AVAILABLE NOW",
        "greeting": "Hello, I'm",
        "name": "KASIF",
        "backdrop": "PORTFOLIO",
        "disciplines": ["AI SOFTWARE ENGINEER &", "BACKEND ARCHITECT"],
        "intro": "I build AI products and the backend systems behind them: LLM pipelines, APIs and data models that hold up in production.",
        "stats": [("3+", "YEARS BUILDING"), ("10+", "PROJECTS SHIPPED"), ("20+", "BRAND COLLABS")],
        "note": "Fast to ship. Built to hold.",
        "chips": [("LLM Apps", 606, 276, 0), ("Node.js APIs", 962, 250, 1.2), ("Data Models", 980, 492, 0.6), ("AI", 1012, 640, 1.8)],
    },
    "projects": [
        {"title": "GitRoasted", "tag": "AI TOOL", "year": "2025", "cover": "gitroasted",
         "subtitle": "Scores any GitHub profile out of 1,000, then lets an AI roast it.",
         "stack": ["Next.js", "TypeScript", "Groq", "Firebase"],
         "href": "https://gitroasted.netlify.app"},
        {"title": "Cookie", "tag": "DESKTOP COMPANION", "year": "2026", "cover": "cookie",
         "subtitle": "A quiet, warm desktop cat for macOS and Windows.",
         "stack": ["Swift", "SwiftUI", "SpriteKit", "Sparkle"],
         "href": "https://cookie-v1.netlify.app/"},
        {"title": "Shadow of the Crimson Gate", "tag": "3D ACTION GAME", "year": "2026", "cover": "shadow-of-the-crimson-gate",
         "subtitle": "A cinematic Japanese dark-fantasy action game, built for the browser.",
         "stack": ["Three.js", "TypeScript", "WebGL"],
         "href": "https://shadow-of-the-crimson-gate.netlify.app/"},
        {"title": "Kerr Black Hole", "tag": "3D SIMULATION", "year": "2026", "cover": "kerr-black-hole",
         "subtitle": "A procedural, Interstellar-inspired rotating black hole in Blender.",
         "stack": ["Blender", "Python", "Cycles"],
         "href": "https://github.com/MdKasif0/black-hole-blender"},
        {"title": "AI Checkers Arena", "tag": "AI ARENA", "year": "2026", "cover": "ai-checkers-arena",
         "subtitle": "Watch large language models battle live in International Checkers.",
         "stack": ["Next.js", "OpenRouter", "Supabase"],
         "href": "https://github.com/MdKasif0/AI-Checkers-Arena"},
        {"title": "Object Detection Suite", "tag": "COMPUTER VISION", "year": "2026", "cover": "object-detection-suite",
         "subtitle": "Production-ready YOLOv8 engines for images, video and live webcam.",
         "stack": ["Python", "YOLOv8", "OpenCV"],
         "href": "https://github.com/MdKasif0/Object-Detection"},
    ],
    "brands": ["hellyeah", "moonshot", "tinyfish", "tavus", "agentmail", "contextdev", "yapper", "molted", "fishaudio", "treg",
               "superapp", "dailydev", "agentid", "shift", "blackbox", "kimi", "unfair", "releasestack", "madeforcollab", "hopper"],
    "recognition": [
        {"title": "GigSense", "result": "1ST RUNNER-UP", "kind": "SOLO HACKATHON · 2026",
         "event": "InnoSprint 2.0 · D4 Community × Google for Developers · Chandigarh University",
         "desc": "A financial intelligence and evidence ledger for gig couriers.", "link": "VIEW CERTIFICATE"},
        {"title": "TrustLayer", "result": None, "kind": "HACKATHON · 2026",
         "event": "Hackverse · Terrabyte Society, Chandigarh University",
         "desc": "Multi-layer media verification.", "link": "VIEW PROJECT"},
    ],
    "about": {
        "statement": "A developer fueled by audacity: convinced every idea is shippable, then actually shipping it.",
        "bio": ["AI software engineer and backend architect, building LLM-powered products, APIs and data systems, plus native desktop apps, from the first sketch to production.",
                "Building in public as a tech creator on X, @md_kasif_uddin."],
        "education": ("B.Tech CSE", "Chandigarh University, Mohali", "1st year, 2026 — now"),
        "stack": [("LANGUAGES", ["TypeScript", "JavaScript", "Python", "Swift"]),
                  ("BACKEND & DATA", ["Node.js", "Supabase", "Firebase", "PostgreSQL"]),
                  ("AI & ML", ["OpenAI", "Gemini", "Hugging Face", "TensorFlow"]),
                  ("FRONTEND", ["React", "Next.js", "Tailwind CSS", "Three.js"]),
                  ("TOOLS", ["Git", "Figma", "Docker", "n8n", "Netlify"])],
        "process": [("The idea", "Start with a need, question or rough sketch worth exploring."),
                    ("The plan", "Map the data model, services and failure paths before building features."),
                    ("The build", "Build the services and the interface together, as one working system."),
                    ("The hardening", "Harden error handling and performance, then refine the details."),
                    ("The launch", "Check the final experience and prepare it to ship.")],
        "quote": "From first idea to production, built to hold up.",
    },
    "journey": {
        "role": "Freelance AI Software Engineer & Backend Architect",
        "period": "2025 — NOW",
        "subtitle": "Freelance · AI software & backend systems",
        "points": ["Designing and building AI-powered software from first idea to production.",
                   "Pairing applied AI with solid backend architecture.",
                   "Taking rough ideas all the way to production."],
        "roles": [("Tech Content Creator on X", "@md_kasif_uddin · AI, dev tools and building in public", "2026"),
                  ("Brand collaborations", "20+ collaborations with AI and tech brands", "2026"),
                  ("B.Tech CSE student", "Chandigarh University, Mohali · First year", "2026")],
        "milestones": [("2025", "Launched GitRoasted"), ("2026", "Shipped GigSense"),
                       ("2026", "20+ brand collaborations"), ("2026", "1st Runner-Up, InnoSprint 2.0")],
    },
    "services": {
        "intro": "Three ways to work together. You talk to the person writing the code, from the first call to the launch.",
        "offers": [
            ("AI product MVP", "2–4 WEEKS", "From an idea to a live product people can actually use.",
             ["LLM pipeline and prompts", "APIs and data model", "A working interface", "Deployed, with real error handling"], "GitRoasted"),
            ("Backend and API build", "1–3 WEEKS", "The services behind a product, built to hold up under real use.",
             ["API design and data modelling", "Auth, storage and integrations", "Limits, caching and failure paths", "Deployment and handover notes"], "AI Checkers Arena"),
            ("AI features for your product", "1–2 WEEKS", "AI added to an app you already run, without breaking what works.",
             ["Chat, search, summaries or scoring", "Model choice and fallbacks", "Cost and prompt limits", "Validated output before users see it"], "GigSense"),
        ],
    },
    "writing": {
        "followers": "6,500+",
        "handle": "@md_kasif_uddin",
        "intro": "Notes on AI, Python and shipping things, written while they're being built.",
        "posts": [("Jan 2026", "Just built a few landing page designs using Stitch. Which one’s the best?", "1.9M", 111, 60),
                  ("Mar 2026", "Just made a quick edit on OpenAI’s AI tools. What do you think?", "130.7K", 160, 39),
                  ("Jan 2026", "Built this real time hand tracking physics engine entirely using Gemini 3 Pro.", "99.8K", 45, 9)],
    },
    "contact": {
        "intro": "Got a product idea? Let's build something worth shipping.",
        "rows": [("Email", "Drop me a line"), ("X", "@md_kasif_uddin"), ("GitHub", "MdKasif0"), ("Portfolio", "kasif-portfolio.netlify.app")],
        "budgets": ["Under $1k", "$1k — $3k", "$3k+"],
    },
}

# ───────────────────────────── themes (the portfolio's own tokens) ─────────────────────────────

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


# ───────────────────────────── sections ─────────────────────────────

def hero(t):
    d = Doc(t, 800)
    c = CONTENT["hero"]
    d.fonts |= {"an", "jk", "cv"}
    # backdrop glow and the giant gradient word
    d.add(glow(d, 930, 400, 560, 420), glow(d, 900, 520, 300, 260, t["glowA"] * .9))
    size = 318
    ww = M["an"].width(c["backdrop"], size, -0.045 * size)
    gx = (W - ww) / 2
    gid = d.uid("word")
    stops = "".join(f'<stop offset="{o}" stop-color="{col}"/>' for o, col in zip((0, .38, .67, 1), t["word"]))
    d.defs.append(f'<linearGradient id="{gid}" x1="0" y1="150" x2="0" y2="470" gradientUnits="userSpaceOnUse">{stops}</linearGradient>')
    d.add(f'<g class="a" style="animation-delay:.05s">'
          f'<text x="{gx:.1f}" y="400" font-size="{size}" class="an" letter-spacing="{-0.045 * size:.1f}" fill="url(#{gid})">{c["backdrop"]}</text></g>')

    # nav bar
    nav = [f'<rect x="24" y="20" width="{W - 48}" height="58" rx="29" fill="{t["nav"]}" stroke="{t["line"]}"/>',
           '<clipPath id="lm"><rect x="40" y="31" width="36" height="36" rx="18"/></clipPath>',
           f'<image href="{asset("logo-mark.png", "image/png")}" x="40" y="31" width="36" height="36" clip-path="url(#lm)"/>',
           d.text(86, 59, "KASIF", 25, t["text"], fam="an", ls=-.4), title_dot(d, 86, 59, "KASIF", 25, -.4)]
    links = ["Work", "Recognition", "About", "Journey", "Services", "Contact"]
    widths = [M["jk"].width(l, 14) for l in links]
    lx = W / 2 - (sum(widths) + 38 * (len(links) - 1)) / 2
    for i, (l, lw) in enumerate(zip(links, widths)):
        nav.append(d.text(lx, 54, l, 14, t["text"] if i == 0 else t["muted"], weight=500))
        if i == 0:
            nav.append(f'<rect x="{lx:.1f}" y="62" width="{lw:.1f}" height="1.5" fill="{t["red"]}"/>')
        lx += lw + 38
    talk, tw = pill(d, W - 40 - 128, 32, "Let's talk", 14, stroke=t["line2"], weight=600, ls=0, padx=18, h=34)
    nav.append(talk + arrow(W - 40 - 128 + tw - 4, 43, 9, t["red2"]))
    d.add(f'<g class="fade">{"".join(nav)}</g>')

    # topline
    d.add(f'<g class="a" style="animation-delay:.3s">{d.text(PAD, 124, c["eyebrow"], 12, t["text2"], weight=600, ls=2.3)}</g>')
    av_w = M["jk"].width(c["availability"], 12, 1.4, 1.045)
    d.add(f'<g class="a" style="animation-delay:.35s">{pulse_dot(d, W - PAD - av_w - 16, 120, t["green"], 3.5)}'
          f'{d.text(W - PAD, 124, c["availability"], 12, t["text2"], weight=600, ls=1.4, anchor="end")}</g>')

    # portrait with the soft rim light and faded bottom edge
    mid = d.uid("fade")
    d.defs.append(f'<linearGradient id="{mid}g" x1="0" y1="0" x2="0" y2="1"><stop offset=".72" stop-color="#fff"/>'
                  f'<stop offset=".86" stop-color="#fff" stop-opacity=".65"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
                  f'<mask id="{mid}" maskContentUnits="objectBoundingBox"><rect width="1" height="1" fill="url(#{mid}g)"/></mask>')
    d.add(f'<g class="a" style="animation-delay:.38s">{glow(d, 905, 510, 290, 300, t["glowA"] * .8)}'
          f'<image href="{asset("avatar.webp", "image/webp")}" x="575" y="160" width="640" height="640" mask="url(#{mid})"/></g>')

    # floating skill chips
    d.css.append("".join(f".fl{i}{{animation:float 5s {dl}s ease-in-out infinite}}" for i, (_, _, _, dl) in enumerate(c["chips"])))
    d.css.append("@keyframes float{50%{transform:translateY(-8px)}}")
    for i, (label, x, y, _) in enumerate(c["chips"]):
        chip, _ = pill(d, x, y, label, 12, fill=t["chip"], stroke=f"rgba({t['glow']},.38)", weight=600, ls=.2, padx=14, h=30)
        d.add(f'<g class="a" style="animation-delay:{1.2 + i * .1:.2f}s"><g class="fl{i}">'
              f'<circle cx="{x + 1}" cy="{y + 15}" r="3" fill="{t["red2"]}"/>{chip}</g></g>')

    # left copy
    copy = [f'<g class="a" style="animation-delay:.68s"><g transform="rotate(-4 {PAD + 8} 290)">'
            f'{d.text(PAD + 8, 300, c["greeting"], 54, t["text"], fam="cv")}</g></g>',
            f'<g class="a" style="animation-delay:.8s">{d.text(PAD - 6, 478, c["name"], 200, t["text"], fam="an", ls=-9)}'
            f'{title_dot(d, PAD - 6, 478, c["name"], 200, -9)}</g>']
    for i, line in enumerate(c["disciplines"]):
        copy.append(f'<g class="a" style="animation-delay:{.92 + i * .06:.2f}s">{d.text(PAD, 522 + i * 28, line, 20, t["red2"], weight=700, ls=3)}</g>')
    intro = wrap(c["intro"], 17, 470)
    for i, line in enumerate(intro):
        copy.append(f'<g class="a" style="animation-delay:{1.04 + i * .06:.2f}s">{d.text(PAD, 596 + i * 27, line, 17, t["text2"])}</g>')
    cta_y = 596 + 27 * len(intro) + 14
    copy.append(f'<g class="a" style="animation-delay:1.18s">'
                f'<rect x="{PAD}" y="{cta_y}" width="168" height="48" rx="4" fill="{t["red2"]}"/>'
                f'{d.text(PAD + 20, cta_y + 30, "See my work", 15, "#FFFFFF", weight=700)}'
                f'<path d="M{PAD + 140} {cta_y + 17}v14m-6-6 6 6 6-6" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
                f'<path d="M{PAD + 200} {cta_y + 17}c-4.5 0-8 3.3-8 7.6 0 5.4 8 12.4 8 12.4s8-7 8-12.4c0-4.3-3.5-7.6-8-7.6z" fill="none" stroke="{t["red"]}" stroke-width="1.5"/>'
                f'<circle cx="{PAD + 200}" cy="{cta_y + 24.5}" r="2.6" fill="none" stroke="{t["red"]}" stroke-width="1.5"/>'
                f'{d.text(PAD + 218, cta_y + 30, "INDIA", 13, t["text2"], weight=700, ls=2.2)}</g>')
    d.add(*copy)

    # stats aside
    sx, sy = 1088, 360
    aside = [f'<rect x="{sx}" y="{sy}" width="156" height="300" rx="16" fill="{t["chip"]}" stroke="{t["line"]}"/>']
    for i, (v, label) in enumerate(c["stats"]):
        yy = sy + 66 + i * 82
        aside.append(d.text(sx + 20, yy, v, 50, t["red"], fam="an"))
        aside.append(d.text(sx + 20, yy + 24, label, 11, t["text2"], weight=600, ls=1.5))
    aside.append(d.text(sx + 20, sy + 280, "DOWNLOAD CV", 11, t["red2"], weight=700, ls=1.5))
    d.add(f'<g class="a" style="animation-delay:1.42s">{d.text(sx + 4, sy - 22, c["note"], 14, t["text2"], italic=True)}'
          f'<text x="{sx - 14}" y="{sy - 20}" font-size="22" fill="{t["red"]}" class="an">“</text></g>',
          f'<g class="a" style="animation-delay:1.54s">{"".join(aside)}</g>')

    # bottom line
    by = 768
    d.add(f'<g class="a" style="animation-delay:1.35s">'
          f'<circle cx="{PAD + 18}" cy="{by - 5}" r="18" fill="none" stroke="{t["red"]}" stroke-opacity=".85"/>'
          f'<path d="M{PAD + 14} {by - 11}l9 6-9 6z" fill="{t["red2"]}"/>'
          f'{d.text(PAD + 50, by, "PLAY REEL", 12, t["text"], weight=700, ls=2.2)}'
          f'<rect x="{PAD + 152}" y="{by - 13}" width="1" height="16" fill="{t["line2"]}"/>'
          f'{d.text(PAD + 166, by, "AI · BACKEND", 11, t["muted"], weight=600, ls=1.2)}</g>',
          f'<g class="fade" style="animation-delay:1.6s">{d.text(W / 2, by, "SCROLL TO DISCOVER +", 11, t["muted"], weight=600, ls=2, anchor="middle")}'
          f'{d.text(W - PAD, by, "SELECTED WORK · 2025–2026", 11, t["muted"], weight=600, ls=2, anchor="end")}</g>')
    return d.render("KASIF — AI Software Engineer & Backend Architect",
                    "Hello, I'm Kasif: AI software engineer and backend architect from India. I build AI products and the backend systems behind them. "
                    "3+ years building, 10+ projects shipped, 20+ brand collaborations. Open to work.")


def section_header(t, number, label, lines, right=None, intro=None):
    """A heading band: eyebrow, Anton headline and an optional right-hand link or intro."""
    d = Doc(t)
    size = 112
    y0 = 92
    body, last = display(d, PAD - 4, y0 + size * .86, lines, size)
    d.add(glow(d, W * .8, 40, 520, 220, t["glowA"] * .6), eyebrow(d, PAD, y0 - 22, label, number), body)
    h = last + 56
    if intro:
        lines_ = wrap(intro, 18, 620)
        for i, line in enumerate(lines_):
            d.add(f'<g class="a" style="animation-delay:.4s">{d.text(PAD, last + 52 + i * 28, line, 18, t["text2"])}</g>')
        h = last + 52 + 28 * len(lines_) + 34
    if right:
        rw = M["jk"].width(right, 13, 2.2, 1.07)
        d.add(f'<g class="a" style="animation-delay:.4s">{d.text(W - PAD - 22, last - 8, right, 13, t["text"], weight=700, ls=2.2, anchor="end")}'
              f'{arrow(W - PAD - 12, last - 19, 10, t["red2"])}'
              f'<rect x="{W - PAD - 22 - rw:.1f}" y="{last + 4}" width="{rw + 22:.1f}" height="1" fill="{t["line2"]}"/></g>')
    d.h = int(h)
    return d


def work_header(t):
    d = section_header(t, "01", "SELECTED WORK", [("WORK THAT SPEAKS", "text")], right="ALL WORK")
    return d.render("01 / Selected work — Work that speaks.")


def project_card(t, p, index):
    d = Doc(t, 560)
    d.w = 440
    d.radius = 18
    cw = d.w
    d.add(f'<rect width="{cw}" height="560" fill="{t["surface"]}"/>')
    # cover image fading into the card, with a slow sheen passing over it
    fid, sheen = d.uid("cover"), d.uid("sheen")
    d.defs.append(f'<linearGradient id="{fid}" x1="0" y1="0" x2="0" y2="1"><stop offset=".45" stop-color="{t["surface"]}" stop-opacity="0"/>'
                  f'<stop offset="1" stop-color="{t["surface"]}"/></linearGradient>'
                  f'<linearGradient id="{sheen}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                  f'<stop offset=".5" stop-color="#fff" stop-opacity=".16"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    d.css.append(f".sh{{animation:sheen 7s {1.5 + index * .6:.1f}s ease-in-out infinite}}"
                 "@keyframes sheen{0%{transform:translateX(-200px)}35%,100%{transform:translateX(640px)}}")
    d.add(f'<g class="fade"><image href="{asset("projects/" + p["cover"] + ".webp", "image/webp")}" x="0" y="0" width="{cw}" height="248" preserveAspectRatio="xMidYMid slice"/>'
          f'<rect width="{cw}" height="250" fill="url(#{fid})"/>'
          f'<g class="sh"><rect x="0" y="0" width="140" height="248" fill="url(#{sheen})" transform="skewX(-18)"/></g></g>')
    tag, _ = pill(d, 18, 18, p["tag"], 11, fill="rgba(5,5,10,.74)", stroke="rgba(255,255,255,.14)", color="#F5F5F5", ls=1.5, h=28)
    d.add(tag)
    # big red number over the bottom right of the cover
    nid = d.uid("num")
    d.defs.append(f'<linearGradient id="{nid}" x1="0" y1="150" x2="0" y2="290" gradientUnits="userSpaceOnUse">'
                  f'<stop offset="0" stop-color="{t["red2"]}"/><stop offset=".7" stop-color="{t["red"]}" stop-opacity=".9"/>'
                  f'<stop offset="1" stop-color="{t["red"]}" stop-opacity=".25"/></linearGradient>')
    d.add(f'<g class="a" style="animation-delay:.25s"><text x="{cw - 20}" y="288" font-size="150" class="an" fill="url(#{nid})" '
          f'text-anchor="end" letter-spacing="-5">{index + 1:02d}</text></g>')
    d.fonts.add("an")
    # title shrinks to fit, wraps when it can't
    title = p["title"].upper()
    size = 38
    while size > 30 and M["an"].width(title, size, -.02 * size) > cw - 44:
        size -= 1
    lines = [title] if M["an"].width(title, size, -.02 * size) <= cw - 44 else wrap(title, size, cw - 44, fam="an")
    y = 330
    out = []
    for line in lines:
        out.append(d.text(22, y, line, size, t["text"], fam="an", ls=-.02 * size))
        y += size * 1.02
    y += 4
    for line in wrap(p["subtitle"], 16.5, cw - 44)[:3]:
        out.append(d.text(22, y, line, 16.5, t["text2"]))
        y += 25
    d.add(f'<g class="a" style="animation-delay:.35s">{"".join(out)}</g>')
    x, chips = 22, []
    for s in p["stack"]:
        chip, w_ = pill(d, x, 462, s, 12, stroke=t["line2"], color=t["text2"], weight=600, ls=.3, padx=11, h=28)
        if x + w_ > cw - 22:
            break
        chips.append(chip)
        x += w_ + 8
    d.add(f'<g class="a" style="animation-delay:.45s">{"".join(chips)}</g>')
    d.add(f'<rect x="22" y="508" width="{cw - 44}" height="1" fill="{t["line"]}"/>',
          d.text(22, 538, p["year"], 13, t["muted"], weight=600, ls=1.5),
          d.text(cw - 44, 538, "OPEN PROJECT", 12, t["red2"], weight=700, ls=1.8, anchor="end"),
          arrow(cw - 34, 528, 10, t["red2"]))
    return d.render(f"{index + 1:02d} — {p['title']}", f"{p['tag'].title()}. {p['subtitle']} Built with {', '.join(p['stack'])}.")


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


def recognition(t):
    d = Doc(t)
    size = 112
    body, last = display(d, PAD - 4, 92 + size * .86, [("THE WORK", "text"), ("THE RECOGNITION", "red")], size)
    d.add(glow(d, W * .85, 120, 500, 260, t["glowA"] * .6), eyebrow(d, PAD, 70, "RECOGNITION & COLLABS"), body)
    y = last + 50
    cols = [("22+", "Hackathons and collaborations"), ("2", "Hackathons"), ("20+", "Brand collaborations")]
    cw = (W - 2 * PAD) / 3
    stats = [f'<rect x="{PAD}" y="{y}" width="{W - 2 * PAD}" height="1" fill="{t["line2"]}"/>']
    for i, (v, label) in enumerate(cols):
        x = PAD + i * cw
        if i:
            stats.append(f'<rect x="{x:.1f}" y="{y}" width="1" height="128" fill="{t["line"]}"/>')
        stats.append(d.text(x + (24 if i else 0), y + 86, v, 76, t["text"] if i else t["red"], fam="an"))
        stats.append(d.text(x + (24 if i else 0), y + 114, label, 14, t["muted"], weight=500))
    d.add(f'<g class="a" style="animation-delay:.3s">{"".join(stats)}</g>')
    y += 160
    for i, e in enumerate(CONTENT["recognition"]):
        row = [f'<rect x="{PAD}" y="{y}" width="{W - 2 * PAD}" height="1" fill="{t["line"]}"/>',
               d.text(PAD, y + 34, e["kind"], 12, t["muted"], weight=700, ls=2.2),
               d.text(PAD - 2, y + 92, e["title"].upper(), 52, t["text"], fam="an", ls=-1)]
        if e["result"]:
            tw = M["an"].width(e["title"].upper(), 52, -1)
            p, _ = pill(d, PAD + tw + 18, y + 58, e["result"], 12, fill=t["red"], color="#FFFFFF", ls=1.6, h=30)
            row.append(p)
        ex, ey = 640, y + 40
        for line in wrap(e["event"], 16, W - PAD - ex - 30, 600):
            row.append(d.text(ex, ey, line, 16, t["text"], weight=600))
            ey += 24
        for line in wrap(e["desc"], 15, W - PAD - ex - 30):
            row.append(d.text(ex, ey + 2, line, 15, t["muted"]))
            ey += 23
        row.append(d.text(ex, ey + 22, e["link"], 12, t["red2"], weight=700, ls=1.8))
        row.append(arrow(ex + M["jk"].width(e["link"], 12, 1.8, 1.07) + 8, ey + 12, 9, t["red2"]))
        d.add(f'<g class="a" style="animation-delay:{.45 + i * .12:.2f}s">{"".join(row)}</g>')
        y = max(y + 130, ey + 50)
    d.h = int(y + 20)
    return d.render("The work. The recognition.",
                    "22+ hackathons and collaborations. GigSense: 1st runner-up, InnoSprint 2.0 (D4 Community × Google for Developers, Chandigarh University). "
                    "TrustLayer: Hackverse, Terrabyte Society. 20+ brand collaborations.")


def about(t):
    d = Doc(t)
    a = CONTENT["about"]
    size = 112
    body, last = display(d, PAD - 4, 92 + size * .86, [("FAST TO SHIP", "text"), ("BUILT TO HOLD", "red")], size)
    d.add(glow(d, 120, 160, 520, 300, t["glowA"] * .55), eyebrow(d, PAD, 70, "HOW I BUILD", "02"), body)
    y = last + 78
    st = [d.text(PAD, y + i * 48, line, 38, t["text"], weight=500, ls=-.8) for i, line in enumerate(wrap(a["statement"], 38, 640, 500))]
    d.add(f'<g class="a" style="animation-delay:.3s">{"".join(st)}</g>')
    rx, ry, right = 820, y - 26, []
    for para in a["bio"]:
        for line in wrap(para, 15, W - PAD - rx):
            right.append(d.text(rx, ry, line, 15, t["text2"]))
            ry += 24
        ry += 12
    right.append(f'<rect x="{rx}" y="{ry}" width="{W - PAD - rx}" height="1" fill="{t["line"]}"/>')
    right.append(d.text(rx, ry + 30, "EDUCATION", 11, t["muted"], weight=700, ls=2))
    deg, school, status = a["education"]
    right.append(d.text(rx, ry + 56, f"{deg} · {school}", 15, t["text"], weight=600))
    right.append(d.text(rx, ry + 80, status, 14, t["muted"]))
    d.add(f'<g class="a" style="animation-delay:.4s">{"".join(right)}</g>')
    y = max(y + 48 * len(st), ry + 80) + 70
    # the stack
    d.add(f'<g class="a" style="animation-delay:.5s">{d.text(PAD, y, "THE STACK", 13, t["red2"], weight=700, ls=2.6)}'
          f'<rect x="{PAD}" y="{y + 18}" width="{W - 2 * PAD}" height="1" fill="{t["line2"]}"/></g>')
    gw = (W - 2 * PAD) / len(a["stack"])
    for i, (label, skills) in enumerate(a["stack"]):
        x = PAD + i * gw
        col = [d.text(x, y + 54, label, 11, t["muted"], weight=700, ls=2)]
        col += [d.text(x, y + 88 + j * 32, s, 19, t["text"], weight=500) for j, s in enumerate(skills)]
        if i:
            col.append(f'<rect x="{x - 16:.1f}" y="{y + 36}" width="1" height="{60 + 32 * 5}" fill="{t["line"]}"/>')
        d.add(f'<g class="a" style="animation-delay:{.55 + i * .07:.2f}s">{"".join(col)}</g>')
    y += 88 + 32 * 5 + 50
    # process timeline with a red line that keeps drawing across it
    d.add(f'<g class="a" style="animation-delay:.7s">{d.text(PAD, y, "FROM IDEA TO FINAL SHIP", 13, t["red2"], weight=700, ls=2.6)}</g>')
    ly = y + 46
    span = W - 2 * PAD
    d.css.append(f".draw{{stroke-dasharray:{span};animation:draw 6s 1s cubic-bezier(.6,0,.2,1) infinite}}"
                 f"@keyframes draw{{0%{{stroke-dashoffset:{span}}}55%,100%{{stroke-dashoffset:0}}}}")
    d.add(f'<rect x="{PAD}" y="{ly - .5}" width="{span}" height="1" fill="{t["line2"]}"/>'
          f'<path class="draw" d="M{PAD} {ly}H{W - PAD}" stroke="{t["red"]}" stroke-width="2"/>')
    sw = span / len(a["process"])
    for i, (title, desc) in enumerate(a["process"]):
        x = PAD + i * sw
        node = [f'<circle cx="{x + 6}" cy="{ly}" r="6" fill="{t["bg"]}" stroke="{t["red"]}" stroke-width="2"/>',
                d.text(x, ly + 54, f"{i + 1:02d}", 30, t["red"], fam="an"),
                d.text(x, ly + 84, title, 18, t["text"], weight=700)]
        node += [d.text(x, ly + 110 + j * 22, line, 14, t["muted"]) for j, line in enumerate(wrap(desc, 14, sw - 30))]
        d.add(f'<g class="a" style="animation-delay:{.8 + i * .1:.2f}s">{"".join(node)}</g>')
    y = ly + 110 + 22 * 3 + 60
    # quote and signature
    sig = "Let's make the next build count."
    d.add(f'<rect x="{PAD}" y="{y - 28}" width="{W - 2 * PAD}" height="1" fill="{t["line"]}"/>',
          f'<g class="a" style="animation-delay:1.2s"><text x="{PAD - 4}" y="{y + 40}" font-size="64" class="an" fill="{t["red"]}">“</text>'
          f'{d.text(PAD + 36, y + 26, a["quote"], 26, t["text"], weight=500, ls=-.4)}'
          f'{d.text(PAD + 36, y + 56, sig, 15, t["muted"])}'
          f'<g transform="rotate(-6 {W - PAD - 110} {y + 30})">{d.text(W - PAD, y + 40, "Kasif", 56, t["red2"], fam="cv", weight=600, anchor="end")}</g></g>')
    d.h = int(y + 92)
    return d.render("02 / How I build — Fast to ship. Built to hold.",
                    a["statement"] + " " + " ".join(a["bio"]) + " Stack: " +
                    "; ".join(f"{l.title()}: {', '.join(s)}" for l, s in a["stack"]) + ".")


def journey(t):
    d = Doc(t)
    j = CONTENT["journey"]
    size = 112
    body, last = display(d, PAD - 4, 92 + size * .86, [("KEEP MOVING", "text"), ("KEEP BUILDING", "red")], size)
    d.add(glow(d, W * .9, 200, 480, 300, t["glowA"] * .55), eyebrow(d, PAD, 70, "THE JOURNEY", "03"), body)
    y = last + 70
    lw = 700
    left = [d.text(PAD, y, "EXPERIENCE", 12, t["muted"], weight=700, ls=2.2),
            f'<rect x="{PAD}" y="{y + 16}" width="{lw}" height="1" fill="{t["line2"]}"/>',
            pulse_dot(d, PAD + 4, y + 50, t["red2"], 4),
            d.text(PAD + 18, y + 55, "NOW", 12, t["red2"], weight=700, ls=2.2),
            d.text(PAD + lw, y + 55, j["period"], 12, t["muted"], weight=700, ls=2, anchor="end")]
    yy = y + 100
    for line in wrap(j["role"], 32, lw, 600):
        left.append(d.text(PAD, yy, line, 32, t["text"], weight=600, ls=-.6))
        yy += 40
    left.append(d.text(PAD, yy + 2, j["subtitle"], 15, t["muted"]))
    yy += 38
    for p in j["points"]:
        left.append(f'<rect x="{PAD}" y="{yy - 6}" width="12" height="2" fill="{t["red"]}"/>')
        left.append(d.text(PAD + 24, yy, p, 16, t["text2"]))
        yy += 28
    yy += 18
    for title, sub, period in j["roles"]:
        left.append(f'<rect x="{PAD}" y="{yy}" width="{lw}" height="1" fill="{t["line"]}"/>')
        left.append(d.text(PAD, yy + 34, title, 18, t["text"], weight=600))
        left.append(d.text(PAD, yy + 58, sub, 14, t["muted"]))
        left.append(d.text(PAD + lw, yy + 34, period, 12, t["muted"], weight=700, ls=2, anchor="end"))
        yy += 80
    d.add(f'<g class="a" style="animation-delay:.3s">{"".join(left)}</g>')
    rx = 840
    rw = W - PAD - rx
    right = [d.text(rx, y, "A FEW MILESTONES", 12, t["muted"], weight=700, ls=2.2),
             f'<rect x="{rx}" y="{y + 16}" width="{rw}" height="1" fill="{t["line2"]}"/>']
    my = y + 16
    for year, title in j["milestones"]:
        right.append(d.text(rx, my + 50, year, 30, t["red"], fam="an"))
        right.append(d.text(rx + 76, my + 46, title, 16, t["text"], weight=500))
        right.append(arrow(rx + rw - 12, my + 33, 10, t["muted"]))
        right.append(f'<rect x="{rx}" y="{my + 72}" width="{rw}" height="1" fill="{t["line"]}"/>')
        my += 72
    d.add(f'<g class="a" style="animation-delay:.45s">{"".join(right)}</g>')
    d.h = int(max(yy, my) + 40)
    return d.render("03 / The journey — Keep moving. Keep building.",
                    f"Now: {j['role']} ({j['period']}). " + " ".join(j["points"]) +
                    " Milestones: " + "; ".join(f"{y_} {m}" for y_, m in j["milestones"]) + ".")


def services(t):
    s = CONTENT["services"]
    d = section_header(t, "04", "WHAT I BUILD", [("WHAT I BUILD", "text")], intro=s["intro"])
    y = d.h + 4
    gap = 22
    cw = (W - 2 * PAD - 2 * gap) / 3
    ch = 420
    for i, (title, timeline, summary, includes, proof_) in enumerate(s["offers"]):
        x = PAD + i * (cw + gap)
        c = [f'<rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="{ch}" rx="16" fill="{t["surface"]}" stroke="{t["line"]}"/>',
             d.text(x + cw - 24, y + 84, f"{i + 1:02d}", 80, t["red"], fam="an", anchor="end", opacity=.16)]
        p, _ = pill(d, x + 26, y + 26, timeline, 11, stroke=f"rgba({t['glow']},.55)", color=t["red2"], ls=1.6, h=28)
        c.append(p)
        ty = y + 100
        for line in wrap(title, 24, cw - 52, 700):
            c.append(d.text(x + 26, ty, line, 24, t["text"], weight=700, ls=-.4))
            ty += 30
        ty += 4
        for line in wrap(summary, 15, cw - 52):
            c.append(d.text(x + 26, ty, line, 15, t["text2"]))
            ty += 23
        ty += 16
        c.append(f'<rect x="{x + 26:.1f}" y="{ty - 14}" width="{cw - 52:.1f}" height="1" fill="{t["line"]}"/>')
        for item in includes:
            c.append(f'<path d="M{x + 27:.1f} {ty + 11}l4 4 8-9" fill="none" stroke="{t["red2"]}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>')
            c.append(d.text(x + 48, ty + 17, item, 14.5, t["text"]))
            ty += 30
        label = f"SEE ONE: {proof_.upper()}"
        c.append(d.text(x + 26, y + ch - 28, label, 11, t["red2"], weight=700, ls=1.6))
        c.append(arrow(x + 26 + M["jk"].width(label, 11, 1.6, 1.07) + 8, y + ch - 37, 9, t["red2"]))
        d.add(f'<g class="a" style="animation-delay:{.35 + i * .12:.2f}s">{"".join(c)}</g>')
    note = "Timelines are typical. I'll confirm yours after a first look at the scope."
    d.add(f'<g class="a" style="animation-delay:.8s">{d.text(PAD, y + ch + 40, note, 13, t["muted"])}</g>')
    d.h = int(y + ch + 72)
    return d.render("04 / What I build — three ways to work together",
                    " ".join(f"{o[0]} ({o[1].lower()}): {o[2]}" for o in s["offers"]))


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


def proof(t, gh):
    w_ = CONTENT["writing"]
    d = section_header(t, None, "BUILDING IN PUBLIC", [("BUILT IN THE OPEN", "text")])
    y = d.h + 10
    d.add(f'<g class="a" style="animation-delay:.3s">{d.text(PAD - 2, y + 70, w_["followers"], 92, t["red"], fam="an")}'
          f'{d.text(PAD, y + 104, "followers on X", 16, t["text"], weight=600)}'
          f'{d.text(PAD, y + 130, w_["handle"], 15, t["muted"])}'
          + "".join(d.text(PAD, y + 172 + i * 23, line, 15, t["text2"]) for i, line in enumerate(wrap(w_["intro"], 15, 330)))
          + "</g>")
    px, gap = 440, 18
    pw = (W - PAD - px - 2 * gap) / 3
    for i, (when, txt, views, likes, replies) in enumerate(w_["posts"]):
        x = px + i * (pw + gap)
        c = [f'<rect x="{x:.1f}" y="{y}" width="{pw:.1f}" height="236" rx="14" fill="{t["surface"]}" stroke="{t["line"]}"/>',
             f'<path d="M{x + 22:.1f} {y + 22}l5.6 7.4-5.9 6.4h1.3l5.2-5.6 4.2 5.6h4.5l-5.9-7.9 5.2-5.9h-1.3l-4.5 5.1-3.8-5.1z" fill="{t["text"]}"/>',
             d.text(x + pw - 22, y + 36, when.upper(), 11, t["muted"], weight=700, ls=1.6, anchor="end")]
        ty = y + 74
        for line in wrap(txt, 14.5, pw - 44)[:3]:
            c.append(d.text(x + 22, ty, line, 14.5, t["text2"]))
            ty += 22
        c.append(d.text(x + 22, y + 192, views, 40, t["text"], fam="an"))
        c.append(d.text(x + 22 + M["an"].width(views, 40) + 10, y + 192, "VIEWS", 11, t["red2"], weight=700, ls=1.6))
        c.append(d.text(x + 22, y + 218, f"{likes} likes · {replies} replies", 12.5, t["muted"]))
        d.add(f'<g class="a" style="animation-delay:{.35 + i * .1:.2f}s">{"".join(c)}</g>')
    y += 290
    # GitHub contribution graph in the portfolio's red levels
    as_of = date.fromisoformat(gh["asOf"]).strftime("%d %b %Y").upper()
    d.add(f'<g class="a" style="animation-delay:.5s">{d.text(PAD, y, "ON GITHUB", 13, t["red2"], weight=700, ls=2.6)}'
          f'{d.text(PAD + 124, y, "@" + USER, 13, t["muted"], weight=600, ls=.4)}'
          f'{d.text(W - PAD, y, "UPDATED DAILY · " + as_of, 11, t["muted"], weight=700, ls=1.6, anchor="end")}'
          f'<rect x="{PAD}" y="{y + 18}" width="{W - 2 * PAD}" height="1" fill="{t["line2"]}"/></g>')
    start = date.fromisoformat(gh["start"])
    first = (start.weekday() + 1) % 7  # GitHub weeks start on Sunday
    weeks = (len(gh["levels"]) + first + 6) // 7
    step = (W - 2 * PAD + 4) / weeks
    cell = step - 4
    gy = y + 66
    cols, months, last_month = {}, [], None
    for i, lvl in enumerate(gh["levels"]):
        wk, dow = divmod(i + first, 7)
        day = start + timedelta(days=i)
        cols.setdefault(wk, []).append(f'<rect x="{PAD + wk * step:.1f}" y="{gy + dow * step:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="3" fill="{t["gh"][int(lvl)]}"/>')
        if day.day <= 7 and dow == 0 and day.month != last_month:
            last_month = day.month
            months.append(d.text(PAD + wk * step, gy - 12, day.strftime("%b"), 11, t["muted"], weight=600))
    d.add("".join(months))
    d.add("".join(f'<g class="fade" style="animation-delay:{.6 + wk * .025:.3f}s">{"".join(r)}</g>' for wk, r in sorted(cols.items())))
    y = gy + 7 * step + 26
    legend = [d.text(W - PAD - 150, y, "Less", 11, t["muted"], weight=600, anchor="end")]
    legend += [f'<rect x="{W - PAD - 142 + i * 20}" y="{y - 11}" width="14" height="14" rx="3" fill="{c}"/>' for i, c in enumerate(t["gh"])]
    legend.append(d.text(W - PAD, y, "More", 11, t["muted"], weight=600, anchor="end"))
    d.add("".join(legend))
    cur, longest = streaks(gh["counts"])
    lp = gh.get("lastPush") or {}
    stats = [(f"{gh['contributions']:,}", "CONTRIBUTIONS, LAST YEAR"), (f"{cur}", "DAY STREAK NOW"), (f"{longest}", "LONGEST STREAK (DAYS)"),
             (f"{gh['repos']}", "PUBLIC REPOS"), (f"{gh['stars']}", "STARS EARNED")]
    y += 34
    sw = (W - 2 * PAD) / len(stats)
    row = [f'<rect x="{PAD}" y="{y}" width="{W - 2 * PAD}" height="1" fill="{t["line"]}"/>']
    for i, (v, label) in enumerate(stats):
        x = PAD + i * sw
        if i:
            row.append(f'<rect x="{x - 16:.1f}" y="{y + 18}" width="1" height="74" fill="{t["line"]}"/>')
        row.append(d.text(x, y + 66, v, 54, t["red"] if i == 0 else t["text"], fam="an"))
        row.append(d.text(x, y + 92, label, 11, t["muted"], weight=700, ls=1.5))
    d.add(f'<g class="a" style="animation-delay:.9s">{"".join(row)}</g>')
    if lp:
        pushed = datetime.fromisoformat(lp["at"].replace("Z", "+00:00"))
        when = f"{pushed.day} {pushed.strftime('%b %Y')}"
        d.add(f'<g class="a" style="animation-delay:1s">{pulse_dot(d, PAD + 4, y + 130, t["green"], 3.5)}'
              f'{d.text(PAD + 18, y + 135, "LAST PUSH", 11, t["muted"], weight=700, ls=1.6)}'
              f'{d.text(PAD + 104, y + 135, lp["repo"], 14, t["text"], weight=600)}'
              f'{d.text(PAD + 112 + M["jk"].width(lp["repo"], 14, bold=1.045), y + 135, "· " + when, 14, t["muted"])}</g>')
    d.h = int(y + 170)
    return d.render("Built in the open — 6,500+ followers on X, plus the GitHub contribution graph",
                    f"{gh['contributions']:,} contributions in the last year, {cur}-day current streak, {longest}-day longest streak, "
                    f"{gh['repos']} public repos, {gh['stars']} stars.")


def contact(t):
    c = CONTENT["contact"]
    d = Doc(t)
    size = 112
    body, last = display(d, PAD - 4, 92 + size * .86, [("LET'S WORK TOGETHER", "text")], size)
    av = CONTENT["hero"]["availability"]
    av_w = M["jk"].width(av, 12, 1.4, 1.045)
    d.add(glow(d, W * .5, 620, 700, 300, t["glowA"] * .9), eyebrow(d, PAD, 70, "YOUR NEXT BUILD", "05"), body,
          f'<g class="a" style="animation-delay:.2s">{pulse_dot(d, W - PAD - av_w - 16, 66, t["green"], 3.5)}'
          f'{d.text(W - PAD, 70, av, 12, t["text2"], weight=600, ls=1.4, anchor="end")}</g>')
    y = last + 76
    intro = [d.text(PAD, y + i * 46, line, 36, t["text"], weight=500, ls=-.8) for i, line in enumerate(wrap(c["intro"], 36, 560, 500))]
    d.add(f'<g class="a" style="animation-delay:.3s">{"".join(intro)}</g>')
    ry = y + 46 * len(intro) + 20
    rows = []
    for label, value in c["rows"]:
        rows.append(f'<rect x="{PAD}" y="{ry}" width="560" height="1" fill="{t["line"]}"/>')
        rows.append(d.text(PAD, ry + 38, label, 13, t["muted"], weight=600))
        rows.append(d.text(PAD + 120, ry + 38, value, 18, t["text"], weight=500))
        rows.append(arrow(PAD + 548, ry + 27, 10, t["red2"]))
        ry += 58
    rows.append(f'<rect x="{PAD}" y="{ry}" width="560" height="1" fill="{t["line"]}"/>')
    d.add(f'<g class="a" style="animation-delay:.4s">{"".join(rows)}</g>')
    # "start a project" card
    fx, fy = 700, y - 36
    fw = W - PAD - fx
    card = [f'<rect x="{fx}" y="{fy}" width="{fw}" height="{ry - fy}" rx="18" fill="{t["surface"]}" stroke="{t["line"]}"/>',
            d.text(fx + 34, fy + 62, "Start a project", 30, t["text"], weight=600, ls=-.6),
            d.text(fx + 34, fy + 92, "Tell me what you're building.", 15, t["muted"])]
    for i, (label, ph) in enumerate([("Name", "Your name"), ("Company", "Where you build")]):
        x = fx + 34 + i * (fw - 68) / 2
        card.append(d.text(x, fy + 140, label, 12, t["muted"], weight=600))
        card.append(d.text(x, fy + 172, ph, 15, t["muted"], opacity=.7))
        card.append(f'<rect x="{x:.1f}" y="{fy + 186}" width="{(fw - 68) / 2 - 24:.1f}" height="1" fill="{t["line2"]}"/>')
    card.append(d.text(fx + 34, fy + 228, "Budget", 12, t["muted"], weight=600))
    bx = fx + 34
    for i, b in enumerate(c["budgets"]):
        p, bw = pill(d, bx, fy + 244, b, 13, fill=t["red"] if i == 1 else None, stroke=None if i == 1 else t["line2"],
                     color="#FFFFFF" if i == 1 else t["text2"], weight=600, ls=.2, padx=16, h=34)
        card.append(p)
        bx += bw + 10
    by = ry - 84
    card.append(f'<rect x="{fx + 34}" y="{by}" width="{fw - 68}" height="54" rx="6" fill="{t["red2"]}"/>')
    card.append(d.text(fx + 58, by + 34, "Tell your project", 16, "#FFFFFF", weight=700))
    card.append(f'<path d="M{fx + fw - 80} {by + 27}h22m-7-7 7 7-7 7" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
    d.add(f'<g class="a" style="animation-delay:.5s">{"".join(card)}</g>')
    fy2 = ry + 70
    d.add(f'<rect x="{PAD}" y="{fy2 - 34}" width="{W - 2 * PAD}" height="1" fill="{t["line2"]}"/>',
          d.text(PAD, fy2, "KASIF", 26, t["text"], fam="an", ls=-.4), title_dot(d, PAD, fy2, "KASIF", 26, -.4),
          d.text(PAD + 100, fy2 - 2, "Fast to ship. Built to hold.  ·  India", 13, t["muted"]),
          d.text(W - PAD, fy2 - 2, "kasif-portfolio.netlify.app", 13, t["text2"], weight=600, anchor="end"))
    d.h = int(fy2 + 32)
    return d.render("05 / Your next build — Let's work together.",
                    "Got a product idea? Let's build something worth shipping. Open to work, available now. "
                    "X @md_kasif_uddin, GitHub MdKasif0, portfolio kasif-portfolio.netlify.app.")


def button(t, label, primary=False, icon=None):
    """A pill for the link row under the contact section."""
    d = Doc(t, 64)
    size, ls = 14, 1.8
    tw = M["jk"].width(label, size, ls, 1.07)
    d.w = int(tw + 76 + (28 if icon else 0))
    d.radius = 32
    fill = t["red2"] if primary else t["surface"]
    color = "#FFFFFF" if primary else t["text"]
    d.add(f'<rect width="{d.w}" height="64" fill="{fill}"/>')
    x = 30
    if icon == "play":
        d.add(f'<circle cx="{x + 9}" cy="32" r="11" fill="none" stroke="{color}" stroke-opacity=".8"/><path d="M{x + 6} 26.5l8 5.5-8 5.5z" fill="{color}"/>')
        x += 30
    d.add(d.text(x, 37, label, size, color, weight=700, ls=ls), arrow(d.w - 36, 27, 10, "#FFFFFF" if primary else t["red2"]))
    return d.render(label.title())


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

    sections = {"hero": hero, "work": work_header, "collabs": collabs, "recognition": recognition,
                "about": about, "journey": journey, "services": services, "contact": contact}
    buttons = {"btn-portfolio": ("VISIT PORTFOLIO", True, None), "btn-reel": ("WATCH THE REEL", False, "play"),
               "btn-email": ("EMAIL ME", False, None), "btn-x": ("FOLLOW ON X", False, None)}
    for name, theme in THEMES.items():
        files = {k: fn(theme) for k, fn in sections.items()}
        files["proof"] = proof(theme, gh)
        for i, p in enumerate(CONTENT["projects"]):
            files[f"project-{i + 1:02d}"] = project_card(theme, p, i)
        for k, (label, primary, icon) in buttons.items():
            files[k] = button(theme, label, primary, icon)
        for k, svg in files.items():
            with open(os.path.join(OUT, f"{k}-{name}.svg"), "w", encoding="utf-8") as f:
                f.write(svg)
        print(f"✅ {name}: {len(files)} SVGs, {sum(len(s) for s in files.values()) / 1024:,.0f} KB")


if __name__ == "__main__":
    main()
