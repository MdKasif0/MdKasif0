#!/usr/env/bin python3
import sys
import json
from datetime import datetime
import os

def render_heatmap(input_file, output_file):
    try:
        with open(input_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {input_file}: {e}")
        return

    # Theme colors for Emerald
    bg_color = "#0A0A0A"
    accent = "#10B981"
    palette = ["#1A1A1A", "#064E3B", "#065F46", "#047857", "#059669", "#10B981"]
    
    # SVG parameters
    box_size = 12
    box_spacing = 3
    week_width = box_size + box_spacing
    total_weeks = 53
    total_width = 860
    total_height = 140
    padding_x = (total_width - (total_weeks * week_width)) // 2
    padding_y = 30
    
    rects = []
    
    # Process weeks (data is flat, assuming 53 weeks * 7 days roughly)
    current_week = 0
    current_day = 0
    
    # Github heatmap starts on Sunday. Let's assume the data is correctly ordered.
    # Group by weeks
    weeks = [data[i:i+7] for i in range(0, len(data), 7)]
    
    # We want a diagonal sweep animation
    for w_idx, week in enumerate(weeks):
        for d_idx, day_data in enumerate(week):
            x = padding_x + w_idx * week_width
            y = padding_y + d_idx * week_width
            
            level = min(5, day_data.get('level', 0))
            color = palette[level]
            
            delay = (w_idx + d_idx) * 0.03
            
            rect = f'''<rect x="{x}" y="{y}" width="{box_size}" height="{box_size}" rx="2" fill="{color}" opacity="0">
                <animate attributeName="opacity" from="0" to="1" dur="0.8s" begin="{delay}s" fill="freeze" />
                <animateTransform attributeName="transform" type="translate" from="0,-10" to="0,0" dur="0.8s" begin="{delay}s" fill="freeze" />
            </rect>'''
            rects.append(rect)

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_width} {total_height}" width="{total_width}" height="{total_height}">
        <style>
            .text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; fill: #94A3B8; font-size: 12px; }}
            .text-accent {{ fill: {accent}; font-weight: bold; }}
        </style>
        <rect width="100%" height="100%" rx="10" fill="{bg_color}" stroke="{accent}" stroke-width="1.5"/>
        <text x="{padding_x}" y="20" class="text">Contributions in the last year</text>
        <text x="{total_width - padding_x}" y="20" class="text" text-anchor="end"><tspan class="text-accent">{len(data)}</tspan> days tracked</text>
        <g>
            {''.join(rects)}
        </g>
    </svg>'''
    
    dirname = os.path.dirname(output_file)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(output_file, "w") as f:
        f.write(svg_content)

if __name__ == "__main__":
    in_file = sys.argv[1] if len(sys.argv) > 1 else "data/contributions.json"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "contrib-heatmap.svg"
    render_heatmap(in_file, out_file)
