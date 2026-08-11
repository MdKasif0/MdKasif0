#!/usr/env/bin python3
import sys
from PIL import Image

def image_to_ascii(image_path, width=100):
    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"Error loading image: {e}")
        sys.exit(1)
        
    # Resize image
    aspect_ratio = img.height / img.width
    # Multiply by 0.5 because font width is about half of font height
    height = int(width * aspect_ratio * 0.55)
    img = img.resize((width, height), Image.LANCZOS)
    img = img.convert("L") # Grayscale
    
    pixels = img.load()
    
    # RAMP from bright (sparse) to dark (dense)
    # The first character is a space so pure white (background) maps to nothing.
    RAMP = " .`:-=+*cs#%@"
    ramp_len = len(RAMP)
    
    ascii_rows = []
    for y in range(height):
        row = ""
        for x in range(width):
            brightness = pixels[x, y]
            # Map 255 (white) to 0, 0 (black) to ramp_len-1
            # We inverted this logic: RAMP[0] is space (bright), RAMP[-1] is @ (dark)
            idx = int((255 - brightness) / 255.0 * (ramp_len - 1))
            row += RAMP[idx]
        ascii_rows.append(row.rstrip())
        
    return ascii_rows, width, height

def generate_svg(ascii_rows, output_path, fill_color="#10B981"):
    font_size = 14
    line_height = 16
    char_width = 8.4
    
    # Calculate dimensions
    max_width = max(len(row) for row in ascii_rows) * char_width
    max_height = len(ascii_rows) * line_height
    
    # Add some padding
    width = int(max_width + 40)
    height = int(max_height + 40)
    
    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">')
    svg_lines.append(f'<style>')
    svg_lines.append(f'  .ascii {{ fill: {fill_color}; font-size: {font_size}px; font-weight: 700; white-space: pre; }}')
    svg_lines.append(f'</style>')
    
    svg_lines.append(f'<g transform="translate(20, 20)">')
    
    base_delay = 0.5
    delay_per_row = 0.05
    wipe_dur = 0.8
    
    for i, row in enumerate(ascii_rows):
        if not row:
            continue
            
        y = (i + 1) * line_height
        delay = base_delay + (i * delay_per_row)
        
        # Each row is clipped by a rectangle that grows from left to right
        clip_id = f"clip-{i}"
        
        svg_lines.append(f'<clipPath id="{clip_id}">')
        svg_lines.append(f'  <rect x="0" y="{y - line_height}" width="0" height="{line_height + 4}">')
        svg_lines.append(f'    <animate attributeName="width" values="0;{width}" dur="{wipe_dur}s" begin="{delay:.2f}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.4 0.0 0.2 1"/>')
        svg_lines.append(f'  </rect>')
        svg_lines.append(f'</clipPath>')
        
        # Add the text with the clip path applied
        # Use xml:space="preserve" to keep leading spaces
        svg_lines.append(f'<text x="0" y="{y}" class="ascii" clip-path="url(#{clip_id})" xml:space="preserve">{row}</text>')
        
        # Add a little "cursor" block that rides the wipe edge
        svg_lines.append(f'<rect x="0" y="{y - line_height + 2}" width="{char_width}" height="{line_height - 2}" fill="{fill_color}" opacity="0">')
        svg_lines.append(f'  <animate attributeName="opacity" values="0;1;1;0" dur="{wipe_dur}s" begin="{delay:.2f}s" fill="freeze" keyTimes="0;0.05;0.95;1"/>')
        svg_lines.append(f'  <animate attributeName="x" values="0;{len(row)*char_width}" dur="{wipe_dur}s" begin="{delay:.2f}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.4 0.0 0.2 1"/>')
        svg_lines.append(f'</rect>')
        
    svg_lines.append(f'</g>')
    svg_lines.append(f'</svg>')
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_lines))
    print(f"Generated {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        input_file = "source-prepped.png"
        output_file = "kasif-ascii.svg"
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        
    rows, w, h = image_to_ascii(input_file, width=85) # slightly narrower for layout
    generate_svg(rows, output_file)
