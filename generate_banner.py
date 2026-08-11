#!/usr/bin/env python3
"""
Generate stipple-art hero banner SVGs for MdKasif0's GitHub profile.
Creates dark.svg and light.svg with animated dot-matrix portrait
that morphs between: profile pic → dev icon → Claude logo → Netlify logo → profile pic
"""

import urllib.request
import io
import math
import random
import sys
import os

# Check for Pillow
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Installing Pillow...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "-q"])
    from PIL import Image, ImageDraw, ImageFont

# ── CONFIG ──
GITHUB_USER = "MdKasif0"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
CANVAS_W, CANVAS_H = 300, 340  # Stipple canvas size (in 1x1 pixel units)
DOT_DENSITY = 5500  # Total number of dots to place
NUM_LAYERS = 12  # Number of animation layers for fade-in
ANIM_DUR = "0.9s"

# ── DOWNLOAD / CREATE SOURCE IMAGES ──

def download_image(url):
    """Download an image from URL and return as PIL Image."""
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    data = urllib.request.urlopen(req, context=ctx).read()
    return Image.open(io.BytesIO(data))

def create_dev_icon(size=400):
    """Create a simple developer/code icon."""
    img = Image.new("L", (size, size), 255)
    draw = ImageDraw.Draw(img)
    
    # Draw code brackets < / >
    cx, cy = size // 2, size // 2
    s = size // 3
    
    # Left bracket <
    draw.line([(cx - s, cy), (cx - s*1.6, cy - s*0.7)], fill=0, width=max(size//25, 4))
    draw.line([(cx - s, cy), (cx - s*1.6, cy + s*0.7)], fill=0, width=max(size//25, 4))
    
    # Right bracket >
    draw.line([(cx + s, cy), (cx + s*1.6, cy - s*0.7)], fill=0, width=max(size//25, 4))
    draw.line([(cx + s, cy), (cx + s*1.6, cy + s*0.7)], fill=0, width=max(size//25, 4))
    
    # Forward slash /
    draw.line([(cx + s*0.5, cy - s*0.9), (cx - s*0.5, cy + s*0.9)], fill=0, width=max(size//25, 4))
    
    # Terminal underscore _
    draw.line([(cx - s*0.3, cy + s*1.2), (cx + s*0.3, cy + s*1.2)], fill=0, width=max(size//20, 3))
    
    return img

def create_claude_icon(size=400):
    """Create Claude AI logo - stylized asterisk/starburst."""
    img = Image.new("L", (size, size), 255)
    draw = ImageDraw.Draw(img)
    
    cx, cy = size // 2, size // 2
    r_outer = size * 0.35
    r_inner = size * 0.12
    num_rays = 6
    ray_width = max(size // 12, 6)
    
    for i in range(num_rays):
        angle = math.pi * 2 * i / num_rays - math.pi / 2
        x1 = cx + math.cos(angle) * r_inner
        y1 = cy + math.sin(angle) * r_inner
        x2 = cx + math.cos(angle) * r_outer
        y2 = cy + math.sin(angle) * r_outer
        draw.line([(x1, y1), (x2, y2)], fill=0, width=ray_width)
        # Rounded end caps
        draw.ellipse([x2 - ray_width//2, y2 - ray_width//2, x2 + ray_width//2, y2 + ray_width//2], fill=0)
    
    # Center circle
    draw.ellipse([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner], fill=0)
    
    return img

def create_netlify_icon(size=400):
    """Create Netlify logo - diamond/parallelogram shape."""
    img = Image.new("L", (size, size), 255)
    draw = ImageDraw.Draw(img)
    
    cx, cy = size // 2, size // 2
    s = size * 0.35
    
    # Diamond shape
    points = [
        (cx, cy - s),      # top
        (cx + s, cy),      # right
        (cx, cy + s),      # bottom
        (cx - s, cy),      # left
    ]
    draw.polygon(points, fill=0)
    
    # Inner cutout - smaller diamond (white)
    s2 = s * 0.5
    points2 = [
        (cx + s2*0.3, cy - s2*0.5),
        (cx + s2, cy + s2*0.1),
        (cx + s2*0.3, cy + s2*0.7),
        (cx - s2*0.3, cy + s2*0.1),
    ]
    draw.polygon(points2, fill=255)
    
    return img


def image_to_stipple_points(img, canvas_w, canvas_h, num_dots):
    """Convert a grayscale image to stipple dot positions using weighted random sampling."""
    # Resize image to canvas size
    img = img.convert("L")
    img = img.resize((canvas_w, canvas_h), Image.LANCZOS)
    
    pixels = img.load()
    
    # Build probability map: darker = higher probability
    weights = []
    coords = []
    for y in range(canvas_h):
        for x in range(canvas_w):
            darkness = 255 - pixels[x, y]
            if darkness > 20:  # Skip very light pixels
                weights.append(darkness)
                coords.append((x, y))
    
    if not weights:
        return []
    
    # Normalize weights
    total = sum(weights)
    probs = [w / total for w in weights]
    
    # Weighted random sampling
    random.seed(42)  # Reproducible
    chosen_indices = random.choices(range(len(coords)), weights=probs, k=num_dots)
    
    # Deduplicate and collect
    seen = set()
    points = []
    for idx in chosen_indices:
        pt = coords[idx]
        if pt not in seen:
            seen.add(pt)
            points.append(pt)
    
    return points


def points_to_svg_path(points):
    """Convert list of (x,y) points to compact SVG path with 1x1 rects."""
    if not points:
        return ""
    
    # Sort by y then x for RLE optimization
    points.sort(key=lambda p: (p[1], p[0]))
    
    parts = []
    i = 0
    while i < len(points):
        x, y = points[i]
        # Check for horizontal run
        run = 1
        while i + run < len(points) and points[i + run][1] == y and points[i + run][0] == x + run:
            run += 1
        
        if run > 1:
            parts.append(f"M{x} {y}h{run}v1h-{run}z")
        else:
            parts.append(f"M{x} {y}h1v1h-1z")
        i += run
    
    return "".join(parts)


def split_into_layers(points, num_layers):
    """Split points into layers for progressive reveal animation."""
    random.seed(123)
    shuffled = list(points)
    random.shuffle(shuffled)
    
    layers = [[] for _ in range(num_layers)]
    for i, pt in enumerate(shuffled):
        layers[i % num_layers].append(pt)
    
    return layers


def build_stipple_group(points, num_layers, base_delay=0.20, fill_color="#00FF41",
                        anim_dur="0.9s", visibility_begin=None, visibility_end=None):
    """Build SVG group with layered stipple animation."""
    layers = split_into_layers(points, num_layers)
    
    lines = []
    
    # Wrapper group with visibility control if needed
    if visibility_begin is not None and visibility_end is not None:
        lines.append(f'<g>')
        # Show at visibility_begin, hide at visibility_end
        lines.append(f'<set attributeName="opacity" to="1" begin="{visibility_begin}s"/>')
        lines.append(f'<set attributeName="opacity" to="0" begin="{visibility_end}s"/>')
    elif visibility_begin is not None:
        lines.append(f'<g opacity="0">')
        lines.append(f'<set attributeName="opacity" to="1" begin="{visibility_begin}s"/>')
    else:
        lines.append('<g>')
    
    for i, layer in enumerate(layers):
        delay = base_delay + i * 0.03
        path_d = points_to_svg_path(layer)
        if not path_d:
            continue
        lines.append(
            f'<g opacity="0"><animate attributeName="opacity" values="0;1" '
            f'dur="{anim_dur}" begin="{delay:.2f}s" fill="freeze" '
            f'calcMode="spline" keyTimes="0;1" keySplines=".4 0 .2 1"/>'
            f'<path d="{path_d}"/></g>'
        )
    
    lines.append('</g>')
    return "\n".join(lines)


def build_morphing_stipple(images_data, canvas_w, canvas_h, num_dots, num_layers,
                           fill_color, cycle_duration=4.0):
    """
    Build multiple stipple groups that cycle through images.
    Each image shows for cycle_duration seconds, then fades to next.
    """
    all_groups = []
    num_images = len(images_data)
    total_cycle = cycle_duration * num_images
    
    for idx, (img, label) in enumerate(images_data):
        points = image_to_stipple_points(img, canvas_w, canvas_h, num_dots)
        
        # Calculate visibility timing
        show_start = idx * cycle_duration
        show_end = show_start + cycle_duration
        
        # Create SVG group with visibility animation
        layers = split_into_layers(points, num_layers)
        
        lines = []
        lines.append(f'<!-- {label} -->')
        
        if idx == 0:
            # First image: visible initially, with fade-in layers
            lines.append(f'<g fill="{fill_color}" shape-rendering="crispEdges">')
            # Hide after first cycle, show again at the end
            lines.append(f'<set attributeName="opacity" to="0" begin="{show_end}s"/>')
            lines.append(f'<set attributeName="opacity" to="1" begin="{total_cycle}s"/>')
            
            for i, layer in enumerate(layers):
                delay = 0.20 + i * 0.03
                path_d = points_to_svg_path(layer)
                if not path_d:
                    continue
                lines.append(
                    f'<g opacity="0"><animate attributeName="opacity" values="0;1" '
                    f'dur="0.9s" begin="{delay:.2f}s" fill="freeze" '
                    f'calcMode="spline" keyTimes="0;1" keySplines=".4 0 .2 1"/>'
                    f'<path d="{path_d}"/></g>'
                )
            lines.append('</g>')
        else:
            # Subsequent images: hidden initially, shown during their window
            lines.append(f'<g fill="{fill_color}" shape-rendering="crispEdges" opacity="0">')
            lines.append(f'<set attributeName="opacity" to="1" begin="{show_start}s"/>')
            lines.append(f'<set attributeName="opacity" to="0" begin="{show_end}s"/>')
            
            for i, layer in enumerate(layers):
                delay = show_start + 0.10 + i * 0.03
                path_d = points_to_svg_path(layer)
                if not path_d:
                    continue
                lines.append(
                    f'<g opacity="0"><animate attributeName="opacity" values="0;1" '
                    f'dur="0.6s" begin="{delay:.2f}s" fill="freeze" '
                    f'calcMode="spline" keyTimes="0;1" keySplines=".4 0 .2 1"/>'
                    f'<path d="{path_d}"/></g>'
                )
            lines.append('</g>')
        
        all_groups.append("\n".join(lines))
    
    return "\n".join(all_groups)


def generate_svg(theme="dark"):
    """Generate the complete hero banner SVG."""
    
    is_dark = theme == "dark"
    
    # Theme colors
    if is_dark:
        bg_primary = "#070B16"
        bg_panel = "#0A101F"
        bg_titlebar = "#0B1222"
        border_subtle = "rgba(255,255,255,0.10)"
        accent = "#00FF41"
        accent_secondary = "#00CC33"
        text_primary = "#F8FAFC"
        text_secondary = "#94A3B8"
        text_muted = "rgba(148,163,184,0.35)"
        dot_color = "#00FF41"
        dot_border_color = "#00FF41"
        label_prefix_color = "#00FF41"
        gradient_stops = ['#00FF41', '#00CC33', '#00FF41']
    else:
        bg_primary = "#F0F4F3"
        bg_panel = "#F8FAF9"
        bg_titlebar = "#EDF2F0"
        border_subtle = "rgba(0,0,0,0.08)"
        accent = "#059669"
        accent_secondary = "#047857"
        text_primary = "#0F172A"
        text_secondary = "#475569"
        text_muted = "rgba(71,85,105,0.30)"
        dot_color = "#047857"
        dot_border_color = "#059669"
        label_prefix_color = "#059669"
        gradient_stops = ['#059669', '#047857', '#059669']
    
    # ── Download/create images ──
    print(f"[{theme}] Downloading profile picture...")
    profile_img = download_image(f"https://github.com/{GITHUB_USER}.png?size=400")
    
    print(f"[{theme}] Creating icon images...")
    dev_img = create_dev_icon(400)
    claude_img = create_claude_icon(400)
    netlify_img = create_netlify_icon(400)
    
    # ── Generate stipple art ──
    print(f"[{theme}] Generating stipple art (this may take a moment)...")
    images_data = [
        (profile_img, "Profile Picture"),
        (dev_img, "Developer Icon"),
        (claude_img, "Claude Logo"),
        (netlify_img, "Netlify Logo"),
    ]
    
    stipple_svg = build_morphing_stipple(
        images_data, CANVAS_W, CANVAS_H, DOT_DENSITY, NUM_LAYERS,
        fill_color=dot_color, cycle_duration=4.0
    )
    
    # ── Build SYSTEM.INFO text lines ──
    info_lines = [
        ("Subject", "Md Kasif Uddin"),
        ("Role", "AI-First Developer"),
        ("Origin", "Bihar, India"),
        ("Education", "Chandigarh University"),
        ("Status", "Building + Learning + Shipping"),
        ("ToolChain", "Claude Code, Git, Supabase, Netlify"),
    ]
    
    core_lines = [
        ("Core.Lang", "Java, TypeScript, Python"),
        ("Core.Frontend", "React, Next.js"),
        ("Core.Backend", "Node.js, Firebase"),
        ("Core.Database", "Supabase, MongoDB, PostgreSQL"),
        ("Core.Infra", "Netlify, Docker, Git"),
    ]
    
    contact_lines = [
        ("Grid.Mail", "mdkasifuddin123@gmail.com"),
        ("Grid.Twitter", "@md_kasif_uddin"),
        ("Grid.GitHub", "@MdKasif0"),
        ("Grid.Instagram", "@md_kasif_uddin"),
    ]
    
    def make_info_text(x, y, label, value, delay, total_width=655):
        dots_count = max(10, 65 - len(label) - len(value))
        dots = "." * dots_count
        return (
            f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.4s" '
            f'begin="{delay:.2f}s" fill="freeze"/><animateTransform attributeName="transform" '
            f'type="translate" values="-8 0;0 0" dur="0.4s" begin="{delay:.2f}s" fill="freeze"/>'
            f'<text x="{x}" y="{y}" font-size="14" textLength="{total_width}" '
            f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">'
            f'<tspan fill="{label_prefix_color}">{label} </tspan>'
            f'<tspan fill="{text_muted}">{dots}</tspan>'
            f'<tspan fill="{text_primary}" font-weight="600"> {value}</tspan>'
            f'</text></g>'
        )
    
    def make_section_line(x, y, label, delay, total_width=655):
        dashes = "-" * (72 - len(label))
        return (
            f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.4s" '
            f'begin="{delay:.2f}s" fill="freeze"/>'
            f'<text x="{x}" y="{y}" font-size="14" textLength="{total_width}" '
            f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">'
            f'<tspan fill="{text_secondary}">- {label} </tspan>'
            f'<tspan fill="{text_muted}">{dashes}</tspan>'
            f'</text></g>'
        )
    
    # Build text SVG
    text_x = 470
    text_y_start = 120
    line_height = 23
    text_svgs = []
    delay = 0.70
    
    # SYSTEM.INFO header
    text_svgs.append(
        f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.4s" '
        f'begin="{delay:.2f}s" fill="freeze"/>'
        f'<text x="{text_x}" y="82" font-size="18" font-weight="700" fill="{accent}">'
        f'SYSTEM.INFO</text>'
        f'<circle cx="1115" cy="77" r="4" fill="#EF4444"><animate attributeName="opacity" '
        f'values="1;0.3;1" dur="2s" repeatCount="indefinite"/></circle>'
        f'<text x="1125" y="82" font-size="11" font-weight="600" fill="#EF4444"> LIVE</text>'
        f'</g>'
    )
    delay += 0.12
    
    # Email badge
    text_svgs.append(
        f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.4s" '
        f'begin="{delay:.2f}s" fill="freeze"/>'
        f'<rect x="{text_x}" y="94" width="220" height="22" rx="3" fill="none" stroke="{accent}" opacity="0.6"/>'
        f'<text x="{text_x + 8}" y="110" font-size="12" fill="{text_primary}">mdkasifuddin123@gmail.com</text>'
        f'</g>'
    )
    delay += 0.20
    
    # Info lines
    y = text_y_start + 20
    for label, value in info_lines:
        text_svgs.append(make_info_text(text_x, y, label, value, delay))
        y += line_height
        delay += 0.12
    
    y += 8  # Gap before core section
    
    for label, value in core_lines:
        text_svgs.append(make_info_text(text_x, y, label, value, delay))
        y += line_height
        delay += 0.12
    
    y += 8  # Gap before contact section
    text_svgs.append(make_section_line(text_x, y, "Contact", delay))
    y += line_height
    delay += 0.12
    
    for label, value in contact_lines:
        text_svgs.append(make_info_text(text_x, y, label, value, delay))
        y += line_height
        delay += 0.12
    
    # Bottom prompt
    y += 8
    text_svgs.append(
        f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" '
        f'begin="{delay:.2f}s" fill="freeze"/>'
        f'<text x="{text_x}" y="{y}" font-size="14" fill="{text_secondary}">'
        f'&#9656; More about me &amp; projects below in README &#8595; '
        f'<tspan fill="{accent}">&#9608;'
        f'<animate attributeName="fill-opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/>'
        f'</tspan></text></g>'
    )
    
    text_block = "\n".join(text_svgs)
    
    # ── Assemble full SVG ──
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="610" viewBox="0 0 1180 610" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace" role="img" aria-label="Md Kasif - profile.sh --live">
<defs>
<linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{gradient_stops[0]}"><animate attributeName="stop-color" values="{gradient_stops[0]};{gradient_stops[1]};{gradient_stops[2]};{gradient_stops[0]}" dur="10s" repeatCount="indefinite"/></stop>
      <stop offset="0.5" stop-color="{gradient_stops[1]}"><animate attributeName="stop-color" values="{gradient_stops[1]};{gradient_stops[2]};{gradient_stops[0]};{gradient_stops[1]}" dur="10s" repeatCount="indefinite"/></stop>
      <stop offset="1" stop-color="{gradient_stops[2]}"><animate attributeName="stop-color" values="{gradient_stops[2]};{gradient_stops[0]};{gradient_stops[1]};{gradient_stops[2]}" dur="10s" repeatCount="indefinite"/></stop>
    </linearGradient>
<linearGradient id="asciiGrad" x1="0" y1="0" x2="0" y2="520" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{accent}"/>
      <stop offset="0.45" stop-color="{accent_secondary}"/>
      <stop offset="1" stop-color="{accent}"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="0 -120; 0 120; 0 -120" dur="9s" repeatCount="indefinite"/>
    </linearGradient>
<linearGradient id="panelGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{bg_panel}"/><stop offset="1" stop-color="{bg_primary}"/></linearGradient>
<filter id="glow8" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="8"/></filter>
<filter id="glow3" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="3"/></filter>
<filter id="txtGlow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="0.9" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<clipPath id="winClip"><rect x="2" y="2" width="1176" height="606" rx="18"/></clipPath>
</defs>
<rect x="2" y="2" width="1176" height="606" rx="18" fill="{bg_primary}"/>
<g clip-path="url(#winClip)">
<rect x="2" y="2" width="1176" height="606" fill="url(#panelGrad)"/>
<rect x="2" y="2" width="1176" height="46" fill="{bg_titlebar}"/>
<line x1="2" y1="48" x2="1178" y2="48" stroke="{border_subtle}"/>
<circle cx="30" cy="25.0" r="5.5" fill="#ff5f56"/>
<circle cx="50" cy="25.0" r="5.5" fill="#ffbd2e"/>
<circle cx="70" cy="25.0" r="5.5" fill="#27c93f"/>
<text x="590.0" y="29.0" text-anchor="middle" font-size="12" fill="{text_secondary}">mdkasifuddin123@gmail.com - % ./profile.sh --live</text>
<text x="38" y="74" font-size="10" letter-spacing="3" fill="{text_secondary}" opacity="0.7">VISUAL.MAP</text>
<rect x="36" y="84" width="400" height="492" rx="10" fill="none" stroke="{dot_border_color}" stroke-width="2" opacity="0.45" filter="url(#glow3)"/>
<rect x="36" y="84" width="400" height="492" rx="10" fill="{bg_panel}" stroke="{'rgba(0,255,65,0.35)' if is_dark else 'rgba(5,150,105,0.35)'}"/>
<g transform="translate(50,86) scale(1.2400,1.4471)" fill="{dot_color}" shape-rendering="crispEdges">
{stipple_svg}
</g>
{text_block}
</g>
<rect x="3" y="3" width="1174" height="604" rx="17" fill="none" stroke="url(#accent)" stroke-width="3" opacity="0.55" filter="url(#glow8)"/>
<rect x="3" y="3" width="1174" height="604" rx="17" fill="none" stroke="url(#accent)" stroke-width="1.6"/>
</svg>'''
    
    return svg


# ── MAIN ──
if __name__ == "__main__":
    print("=" * 60)
    print("Generating hero banner SVGs for MdKasif0")
    print("=" * 60)
    
    for theme in ["dark", "light"]:
        print(f"\n--- Generating {theme}.svg ---")
        svg_content = generate_svg(theme)
        
        output_path = os.path.join(OUTPUT_DIR, f"{theme}.svg")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        
        file_size = os.path.getsize(output_path)
        print(f"✅ Written {output_path} ({file_size:,} bytes)")
    
    print("\n" + "=" * 60)
    print("Done! Both dark.svg and light.svg have been generated.")
    print("=" * 60)
