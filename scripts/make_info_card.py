#!/usr/env/bin python3
import sys

def generate_neofetch(output_path):
    # Colors matching the Emerald professional theme
    accent = "#10B981"
    text_primary = "#F8FAFC"
    bg_color = "#0A0A0A"
    
    font_family = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
    
    lines_data = [
        ("Role", "AI-First Developer"),
        ("Origin", "Bihar, India"),
        ("Education", "Chandigarh University"),
        ("Status", "Building + Learning + Shipping"),
        ("ToolChain", "Claude Code, Git, Supabase, Netlify"),
        ("Lang", "Java, TypeScript, Python"),
        ("Frontend", "React, Next.js"),
        ("Backend", "Node.js, Firebase"),
        ("Database", "Supabase, MongoDB, PostgreSQL")
    ]
    
    # SVG setup
    width = 490
    height = 360 # Adjusted for content
    
    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="{font_family}">')
    svg_lines.append(f'<rect width="100%" height="100%" fill="{bg_color}" rx="8" opacity="0"/>') # transparent background since it's on README
    
    # Neofetch Title
    svg_lines.append(f'<text x="20" y="40" font-size="16" font-weight="bold" fill="{accent}">mdkasif@github</text>')
    svg_lines.append(f'<text x="20" y="55" font-size="16" font-weight="bold" fill="{text_primary}">--------------</text>')
    
    y_start = 85
    line_height = 24
    base_delay = 0.5
    delay_per_line = 0.15
    
    for i, (key, value) in enumerate(lines_data):
        y = y_start + (i * line_height)
        delay = base_delay + (i * delay_per_line)
        
        # Calculate animation for each line
        # The line fades and slides in from the left slightly
        svg_lines.append(f'<g opacity="0">')
        svg_lines.append(f'  <animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{delay:.2f}s" fill="freeze" />')
        svg_lines.append(f'  <animateTransform attributeName="transform" type="translate" values="-10 0;0 0" dur="0.5s" begin="{delay:.2f}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.4 0.0 0.2 1"/>')
        
        # Draw Key
        svg_lines.append(f'  <text x="20" y="{y}" font-size="15" font-weight="bold" fill="{accent}">{key}</text>')
        # Draw Separator (colon)
        svg_lines.append(f'  <text x="110" y="{y}" font-size="15" font-weight="bold" fill="{text_primary}">:</text>')
        # Draw Value
        svg_lines.append(f'  <text x="130" y="{y}" font-size="15" fill="{text_primary}">{value}</text>')
        
        svg_lines.append(f'</g>')
        
    # Color blocks at the bottom (like neofetch usually has)
    blocks_y = y_start + (len(lines_data) * line_height) + 20
    delay = base_delay + (len(lines_data) * delay_per_line)
    
    colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#10B981"]
    
    svg_lines.append(f'<g opacity="0">')
    svg_lines.append(f'  <animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{delay:.2f}s" fill="freeze" />')
    for idx, c in enumerate(colors):
        x = 20 + (idx * 24)
        svg_lines.append(f'  <rect x="{x}" y="{blocks_y}" width="16" height="16" fill="{c}"/>')
    svg_lines.append(f'</g>')
    
    svg_lines.append(f'</svg>')
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_lines))
    print(f"Generated {output_path}")

if __name__ == "__main__":
    output_file = sys.argv[1] if len(sys.argv) > 1 else "info-card.svg"
    generate_neofetch(output_file)
