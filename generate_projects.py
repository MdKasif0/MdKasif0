#!/usr/bin/env python3
"""Generate projects.svg for MdKasif0's GitHub profile README."""

import math

# ── Project Data (from GitHub API) ──
PROJECTS = [
    {
        "repo": "MdKasif0/GitRoasted",
        "name": "GitRoasted",
        "desc": "Analyze, Roast & Rank Your GitHub Profile",
        "langs": {"TypeScript": 96, "CSS": 3, "Other": 1},
        "tags": ["Next.js", "Firebase", "OpenAI"],
        "stars": 19,
        "updated": "1d ago",
    },
    {
        "repo": "MdKasif0/comment_tracker",
        "name": "CommentTracker",
        "desc": "Productivity tool to track code comments",
        "langs": {"JavaScript": 73, "HTML": 27},
        "tags": ["JavaScript", "HTML"],
        "stars": 2,
        "updated": "2mo ago",
    },
    {
        "repo": "MdKasif0/bigbang-simulation",
        "name": "BigBang Sim",
        "desc": "Interactive Big Bang universe simulation",
        "langs": {"TypeScript": 88, "CSS": 7, "HTML": 5},
        "tags": ["TypeScript", "WebGL", "CSS"],
        "stars": 1,
        "updated": "2w ago",
    },
    {
        "repo": "MdKasif0/AI-Checkers-Arena",
        "name": "AI Checkers Arena",
        "desc": "AI-powered checkers game with smart opponents",
        "langs": {"TypeScript": 93, "CSS": 6, "JS": 1},
        "tags": ["TypeScript", "AI", "CSS"],
        "stars": 1,
        "updated": "3w ago",
    },
    {
        "repo": "MdKasif0/Magnetar-Magnetic-Storm-Simulator",
        "name": "Magnetar Sim",
        "desc": "Magnetar magnetic storm visualization",
        "langs": {"TypeScript": 95, "CSS": 4, "HTML": 1},
        "tags": ["TypeScript", "WebGL"],
        "stars": 1,
        "updated": "3w ago",
    },
    {
        "repo": "MdKasif0/black-hole-blender",
        "name": "BlackHole Blender",
        "desc": "Black hole visualization in Blender with Python",
        "langs": {"Python": 100},
        "tags": ["Python", "Blender"],
        "stars": 1,
        "updated": "1w ago",
    },
]

# ── Theme Colors ──
BG = "#0A0A0A"
CARD_BG = "#111111"
CARD_HEADER_BG = "#0D0D0D"
BORDER_COLOR = "rgba(0,255,65,0.28)"
BORDER_GLOW = "rgba(0,255,65,0.22);rgba(0,255,65,0.5);rgba(0,255,65,0.22)"
ACCENT = "#00FF41"
TEXT_PRIMARY = "#F8FAFC"
TEXT_SECONDARY = "#94A3B8"
TEXT_MUTED = "#475569"
DOT_ACTIVE = "#00FF41"
HEADER_LINE = "rgba(255,255,255,0.08)"

# Language colors
LANG_COLORS = {
    "TypeScript": "#3178C6",
    "JavaScript": "#F7DF1E",
    "Python": "#3776AB",
    "CSS": "#563D7C",
    "HTML": "#E34C26",
    "GLSL": "#5686A5",
    "Other": "#6B7280",
    "JS": "#F7DF1E",
}

TAG_COLORS = {
    "Next.js": "#000000",
    "Firebase": "#FFCA28",
    "OpenAI": "#412991",
    "TypeScript": "#3178C6",
    "JavaScript": "#F7DF1E",
    "Python": "#3776AB",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
    "WebGL": "#990000",
    "AI": "#00FF41",
    "Blender": "#F5792A",
}

CARD_W = 578
CARD_H = 168
COL_GAP = 9
ROW_GAP = 9
COLS = 2
MARGIN_X = 5
MARGIN_TOP = 42


def donut_chart_svg(cx, cy, r_outer, r_inner, langs, size_label):
    """Generate a donut chart SVG."""
    parts = []
    
    # Background circle
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r_outer}" fill="#1a1a1a" stroke="rgba(0,255,65,0.1)" stroke-width="1"/>')
    
    # Draw segments
    total = sum(langs.values())
    start_angle = -90  # Start from top
    
    for lang, pct in langs.items():
        if pct <= 0:
            continue
        sweep = (pct / total) * 360
        end_angle = start_angle + sweep
        
        # Calculate arc path
        large_arc = 1 if sweep > 180 else 0
        
        sx = cx + r_outer * math.cos(math.radians(start_angle))
        sy = cy + r_outer * math.sin(math.radians(start_angle))
        ex = cx + r_outer * math.cos(math.radians(end_angle))
        ey = cy + r_outer * math.sin(math.radians(end_angle))
        
        isx = cx + r_inner * math.cos(math.radians(end_angle))
        isy = cy + r_inner * math.sin(math.radians(end_angle))
        iex = cx + r_inner * math.cos(math.radians(start_angle))
        iey = cy + r_inner * math.sin(math.radians(start_angle))
        
        color = LANG_COLORS.get(lang, "#6B7280")
        
        path = (
            f'M{sx:.1f},{sy:.1f} '
            f'A{r_outer},{r_outer} 0 {large_arc} 1 {ex:.1f},{ey:.1f} '
            f'L{isx:.1f},{isy:.1f} '
            f'A{r_inner},{r_inner} 0 {large_arc} 0 {iex:.1f},{iey:.1f} Z'
        )
        parts.append(f'<path d="{path}" fill="{color}" opacity="0.85"/>')
        
        start_angle = end_angle
    
    # Center text (percentage of primary language)
    primary_pct = list(langs.values())[0]
    parts.append(
        f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" font-size="14" '
        f'font-weight="700" fill="{TEXT_PRIMARY}">{primary_pct}%</text>'
    )
    
    return "\n".join(parts)


def lang_legend_svg(x, y, langs):
    """Generate language legend dots + text."""
    parts = []
    ly = y
    for lang, pct in langs.items():
        color = LANG_COLORS.get(lang, "#6B7280")
        parts.append(f'<circle cx="{x}" cy="{ly - 3}" r="3" fill="{color}"/>')
        parts.append(
            f'<text x="{x + 8}" y="{ly}" font-size="10" fill="{TEXT_SECONDARY}">'
            f'{lang} {pct}%</text>'
        )
        ly += 16
    return "\n".join(parts)


def tag_badge_svg(x, y, tag):
    """Generate a rounded tag badge."""
    color = TAG_COLORS.get(tag, "#333")
    text_len = len(tag) * 6.5 + 14
    return (
        f'<rect x="{x}" y="{y}" width="{text_len:.0f}" height="20" rx="4" '
        f'fill="{color}" opacity="0.7"/>'
        f'<text x="{x + text_len/2:.0f}" y="{y + 14}" text-anchor="middle" '
        f'font-size="10" font-weight="600" fill="{TEXT_PRIMARY}">{tag}</text>'
    )


def project_card_svg(proj, card_x, card_y, delay):
    """Generate a single project card."""
    parts = []
    
    # Card container with animated border
    parts.append(f'<a href="https://github.com/{proj["repo"]}" target="_blank">')
    parts.append(f'<g opacity="0" transform="translate({card_x},{card_y})">')
    parts.append(
        f'<animate attributeName="opacity" from="0" to="1" dur="0.5s" '
        f'begin="{delay:.2f}s" fill="freeze"/>'
    )
    
    # Card background
    parts.append(
        f'<rect width="{CARD_W}" height="{CARD_H}" rx="12" fill="{CARD_BG}" '
        f'stroke="{BORDER_COLOR}">'
        f'<animate attributeName="stroke" values="{BORDER_GLOW}" '
        f'dur="4.5s" begin="{delay:.2f}s" repeatCount="indefinite"/></rect>'
    )
    
    # Header bar
    parts.append(f'<rect width="{CARD_W}" height="30" rx="12" fill="{CARD_HEADER_BG}"/>')
    parts.append(f'<rect y="18" width="{CARD_W}" height="12" fill="{CARD_HEADER_BG}"/>')
    parts.append(f'<line x1="0" y1="30" x2="{CARD_W}" y2="30" stroke="{HEADER_LINE}"/>')
    
    # Repo path in header
    parts.append(
        f'<text x="16" y="19" font-size="10" fill="{TEXT_SECONDARY}">'
        f'<tspan fill="{ACCENT}">&#8226;</tspan> {proj["repo"]}</text>'
    )
    
    # Status dot
    parts.append(
        f'<circle cx="{CARD_W - 16}" cy="15" r="3.5" fill="{DOT_ACTIVE}">'
        f'<animate attributeName="opacity" values="1;0.25;1" dur="1.8s" '
        f'repeatCount="indefinite"/></circle>'
    )
    
    # Project name
    import html
    safe_name = html.escape(proj["name"])
    parts.append(
        f'<text x="16" y="63" font-size="22" font-weight="700" fill="{TEXT_PRIMARY}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,monospace">'
        f'{safe_name}<tspan fill="{ACCENT}" font-weight="400">_</tspan></text>'
    )
    
    # Description
    desc = proj["desc"]
    if len(desc) > 48:
        desc = desc[:45] + "..."
    safe_desc = html.escape(desc)
    parts.append(
        f'<text x="16" y="82" font-size="12" fill="{TEXT_SECONDARY}">{safe_desc}</text>'
    )
    
    # Language breakdown legend
    legend_x = 340
    legend_y = 62
    parts.append(lang_legend_svg(legend_x, legend_y, proj["langs"]))
    
    # Donut chart
    parts.append(donut_chart_svg(CARD_W - 45, 72, 25, 16, proj["langs"], ""))
    
    # Tags
    tag_x = 16
    for tag in proj["tags"]:
        parts.append(tag_badge_svg(tag_x, 110, tag))
        tag_x += len(tag) * 6.5 + 14 + 6
    
    # Stars and update time
    parts.append(
        f'<text x="16" y="152" font-size="10" fill="{TEXT_MUTED}">'
        f'<tspan fill="{ACCENT}">★</tspan> {proj["stars"]}  '
        f'updated {proj["updated"]}</text>'
    )
    
    parts.append('</g></a>')
    
    return "\n".join(parts)


def generate_projects_svg():
    """Generate the full projects.svg."""
    num_rows = math.ceil(len(PROJECTS) / COLS)
    total_h = MARGIN_TOP + num_rows * (CARD_H + ROW_GAP) + 10
    
    svg_parts = []
    
    # SVG header
    svg_parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="{total_h}" '
        f'viewBox="0 0 1180 {total_h}" '
        f'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,\'Liberation Mono\',monospace" '
        f'role="img" aria-label="Projects">'
    )
    
    # Background
    svg_parts.append(f'<rect width="1180" height="{total_h}" fill="{BG}"/>')
    
    # Gradient defs
    svg_parts.append('''<defs>
<linearGradient id="acc_line" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#00FF41">
    <animate attributeName="stop-color" values="#00FF41;#00CC33;#00FF41" dur="10s" repeatCount="indefinite"/>
  </stop>
  <stop offset="1" stop-color="#00CC33">
    <animate attributeName="stop-color" values="#00CC33;#00FF41;#00CC33" dur="10s" repeatCount="indefinite"/>
  </stop>
</linearGradient>
</defs>''')
    
    # Header
    svg_parts.append(
        f'<text x="7" y="18" font-size="11" letter-spacing="2" fill="{ACCENT}">'
        f'PROJECTS.LIST</text>'
    )
    svg_parts.append(
        f'<text x="135" y="18" font-size="10" fill="{TEXT_MUTED}">'
        f'./projects.sh --all</text>'
    )
    svg_parts.append(
        '<line x1="5" y1="28" x2="1175" y2="28" stroke="url(#acc_line)" '
        'stroke-width="1.5" opacity="0.7"/>'
    )
    
    # Project cards
    delay = 0.25
    for i, proj in enumerate(PROJECTS):
        col = i % COLS
        row = i // COLS
        
        card_x = MARGIN_X + col * (CARD_W + COL_GAP)
        card_y = MARGIN_TOP + row * (CARD_H + ROW_GAP)
        
        svg_parts.append(project_card_svg(proj, card_x, card_y, delay))
        delay += 0.18
    
    svg_parts.append('</svg>')
    
    return "\n".join(svg_parts)


if __name__ == "__main__":
    svg = generate_projects_svg()
    
    import os
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "projects.svg")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    
    print(f"✅ Written {output_path} ({os.path.getsize(output_path):,} bytes)")
