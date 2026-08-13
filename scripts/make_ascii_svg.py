#!/usr/env/bin python3
import sys
import os
from PIL import Image

def image_to_ascii(img_path, width=100, height=53):
    if not os.path.exists(img_path):
        return []
    
    img = Image.open(img_path).convert("L")
    img = img.resize((width, height), Image.LANCZOS)
    
    RAMP = " .`:-=+*cs#%@"
    pixels = img.load()
    
    lines = []
    for y in range(height):
        row = []
        for x in range(width):
            val = pixels[x, y]
            # Map 0-255 to RAMP index (darker = denser)
            idx = int((255 - val) / 255 * (len(RAMP) - 1))
            row.append(RAMP[idx])
        lines.append("".join(row))
        
    return lines

def generate_ascii_svg(output_path):
    # Load profile pic and dev logo
    profile_lines = image_to_ascii("source-prepped.png")
    dev_lines = image_to_ascii("extracted_dev_logo.png")
    
    # If one is missing, fallback to the other
    if not profile_lines and dev_lines:
        profile_lines = dev_lines
    elif not dev_lines and profile_lines:
        dev_lines = profile_lines
        
    width = 370
    height = 500
    
    font_size = 9
    line_height = 9.4
    
    # We will build the SVG
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">']
    svg.append(f'<style> text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: {font_size}px; white-space: pre; }} </style>')
    
    # Background
    svg.append(f'<rect width="100%" height="100%" rx="10" fill="#0A0A0A" stroke="#10B981" stroke-width="1.5" />')
    
    # Profile Picture Group
    # It will wipe in from t=0 to t=3, stay until t=5, then fade out at t=5.
    svg.append('<g>')
    svg.append('<animate attributeName="opacity" values="1;1;0" keyTimes="0;0.9;1" dur="5.5s" fill="freeze" />')
    for y, line_text in enumerate(profile_lines):
        y_pos = 20 + y * line_height
        delay = y * 0.05
        # We use a clip path to wipe it in
        clip_id = f"clip-prof-{y}"
        svg.append(f'<clipPath id="{clip_id}">')
        svg.append(f'<rect x="0" y="{y_pos - 10}" width="0" height="{line_height + 5}">')
        svg.append(f'<animate attributeName="width" from="0" to="{width}" dur="0.8s" begin="{delay}s" fill="freeze" />')
        svg.append('</rect></clipPath>')
        
        # We add the text using this clip path
        svg.append(f'<text x="10" y="{y_pos}" fill="#10B981" clip-path="url(#{clip_id})">{line_text}</text>')
        
        # Adding a cursor block that follows the wipe
        svg.append(f'<rect x="10" y="{y_pos - 8}" width="8" height="10" fill="#34D399" opacity="0">')
        svg.append(f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;0.1;1" dur="0.8s" begin="{delay}s" fill="freeze" />')
        svg.append(f'<animate attributeName="x" from="10" to="{width}" dur="0.8s" begin="{delay}s" fill="freeze" />')
        svg.append('</rect>')
    svg.append('</g>')
    
    # Developer Logo Group
    # It stays opacity 0 until t=5.5, then types out!
    svg.append('<g opacity="0">')
    svg.append('<animate attributeName="opacity" values="0;1" dur="0.1s" begin="5.5s" fill="freeze" />')
    for y, line_text in enumerate(dev_lines):
        y_pos = 20 + y * line_height
        delay = 5.5 + y * 0.05
        
        clip_id = f"clip-dev-{y}"
        svg.append(f'<clipPath id="{clip_id}">')
        svg.append(f'<rect x="0" y="{y_pos - 10}" width="0" height="{line_height + 5}">')
        svg.append(f'<animate attributeName="width" from="0" to="{width}" dur="0.8s" begin="{delay}s" fill="freeze" />')
        svg.append('</rect></clipPath>')
        
        svg.append(f'<text x="10" y="{y_pos}" fill="#34D399" clip-path="url(#{clip_id})">{line_text}</text>')
        
        svg.append(f'<rect x="10" y="{y_pos - 8}" width="8" height="10" fill="#10B981" opacity="0">')
        svg.append(f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;0.1;1" dur="0.8s" begin="{delay}s" fill="freeze" />')
        svg.append(f'<animate attributeName="x" from="10" to="{width}" dur="0.8s" begin="{delay}s" fill="freeze" />')
        svg.append('</rect>')
    svg.append('</g>')
    
    svg.append('</svg>')
    
    dirname = os.path.dirname(output_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(svg))

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "kasif-ascii.svg"
    generate_ascii_svg(out_file)
