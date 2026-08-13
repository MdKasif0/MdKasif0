#!/usr/env/bin python3
import sys
import os

def generate_neofetch(output_path):
    # Colors matching the Emerald professional theme
    accent = "#10B981"
    text_primary = "#F8FAFC"
    text_secondary = "#94A3B8"
    bg_color = "#0A0A0A"
    
    font_family = "ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,Liberation Mono,Courier New,monospace"
    
    # We will fade in line by line. Let's make an inner function for rows
    # so we can manage the staggering delay easily.
    lines_svg = []
    y_pos = 70
    delay = 0.2
    
    def add_line(key, value, color_key=accent, is_title=False):
        nonlocal y_pos, delay
        if is_title:
            lines_svg.append(f'''
            <g opacity="0">
                <animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{delay}s" fill="freeze" />
                <animateTransform attributeName="transform" type="translate" from="-10, 0" to="0, 0" dur="0.5s" begin="{delay}s" fill="freeze" />
                <text x="30" y="{y_pos}" font-family="{font_family}" font-weight="bold" font-size="16" fill="{color_key}">{key}</text>
                <text x="30" y="{y_pos+5}" font-family="{font_family}" font-size="16" fill="{text_secondary}">{"-" * 35}</text>
            </g>
            ''')
            y_pos += 30
        else:
            lines_svg.append(f'''
            <g opacity="0">
                <animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{delay}s" fill="freeze" />
                <animateTransform attributeName="transform" type="translate" from="-10, 0" to="0, 0" dur="0.5s" begin="{delay}s" fill="freeze" />
                <text x="30" y="{y_pos}" font-family="{font_family}" font-weight="bold" font-size="14" fill="{color_key}">{key}</text>
                <text x="140" y="{y_pos}" font-family="{font_family}" font-size="14" fill="{text_primary}">{value}</text>
            </g>
            ''')
            y_pos += 24
        delay += 0.15

    add_line("mdkasifuddin@github", "", is_title=True)
    add_line("Subject", "Md Kasif Uddin")
    add_line("Role", "AI-First Developer")
    add_line("Origin", "Bihar, India")
    add_line("Education", "Chandigarh University")
    add_line("Status", "Building + Learning + Shipping")
    
    y_pos += 15
    add_line("Core.Lang", "Java, TypeScript, Python")
    add_line("Core.Frontend", "React, Next.js")
    add_line("Core.Backend", "Node.js, Firebase")
    add_line("Core.Database", "Supabase, MongoDB, PostgreSQL")
    add_line("Core.Infra", "Netlify, Docker, Git")
    
    y_pos += 15
    add_line("Grid.Mail", "mdkasifuddin123@gmail.com")
    add_line("Grid.Twitter", "@md_kasif_uddin")
    add_line("Grid.GitHub", "@MdKasif0")
    add_line("Grid.Instagram", "@md_kasif_uddin")
    
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 490 500" width="490" height="500">
    <rect width="100%" height="100%" rx="10" fill="{bg_color}" stroke="{accent}" stroke-width="1.5" />
    
    <!-- Mac window buttons -->
    <circle cx="20" cy="20" r="6" fill="#EF4444" />
    <circle cx="40" cy="20" r="6" fill="#EAB308" />
    <circle cx="60" cy="20" r="6" fill="#22C55E" />
    
    <!-- Title -->
    <text x="245" y="24" font-family="{font_family}" font-size="12" fill="{text_secondary}" text-anchor="middle">kasif@github: ~/profile - ./system.live</text>
    <line x1="0" y1="40" x2="490" y2="40" stroke="{accent}" stroke-width="1.5" />

    {''.join(lines_svg)}
    </svg>'''
    
    dirname = os.path.dirname(output_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(svg_content)
    
if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "info-card.svg"
    generate_neofetch(out_file)
