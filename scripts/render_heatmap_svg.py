#!/usr/env/bin python3
import sys
import json
from datetime import datetime

def render_heatmap(input_file, output_file):
    try:
        with open(input_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        sys.exit(1)
        
    contributions = data.get("contributions", [])
    if not contributions:
        print("No contributions found in JSON.")
        sys.exit(1)
        
    # Build grid (weeks x 7 days)
    weeks = []
    current_week = []
    
    # We just pack the days into columns of 7.
    # Note: GitHub calendar might not start on a Sunday depending on the exact date range,
    # but for visual purposes, packing them 7-per-column works.
    for c in contributions:
        current_week.append(c)
        if len(current_week) == 7:
            weeks.append(current_week)
            current_week = []
            
    if current_week:
        weeks.append(current_week)
        
    # Visual configuration
    box_size = 12
    box_spacing = 3
    
    total_width = 860
    # Center the grid inside the 860 width
    grid_width = len(weeks) * (box_size + box_spacing) - box_spacing
    grid_height = 7 * (box_size + box_spacing) - box_spacing
    
    start_x = (total_width - grid_width) // 2
    start_y = 40 # margin top
    
    # Emerald professional palette
    # Level 0, 1, 2, 3, 4
    palette = ["#161b22", "#0e4429", "#006d32", "#26a641", "#10B981"]
    
    svg_lines = []
    total_height = start_y + grid_height + 40
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{total_height}" viewBox="0 0 {total_width} {total_height}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">')
    
    # Title
    svg_lines.append(f'<text x="20" y="24" font-size="14" font-weight="bold" fill="#F8FAFC">Contributions Heatmap (Last 12 Months)</text>')
    
    svg_lines.append(f'<g transform="translate({start_x}, {start_y})">')
    
    # Animation properties
    base_delay = 0.5
    
    for w_idx, week in enumerate(weeks):
        for d_idx, day in enumerate(week):
            level = min(day.get("level", 0), 4)
            color = palette[level]
            
            x = w_idx * (box_size + box_spacing)
            y = d_idx * (box_size + box_spacing)
            
            # Diagonal slide down animation
            # Delay based on diagonal distance (x + y)
            delay = base_delay + (w_idx * 0.02) + (d_idx * 0.04)
            
            svg_lines.append(f'<rect x="{x}" y="{y}" width="{box_size}" height="{box_size}" rx="2" fill="{color}" opacity="0">')
            svg_lines.append(f'  <animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="{delay:.2f}s" fill="freeze" />')
            svg_lines.append(f'  <animateTransform attributeName="transform" type="translate" values="0 -10;0 0" dur="0.4s" begin="{delay:.2f}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.4 0.0 0.2 1"/>')
            svg_lines.append(f'</rect>')
            
    svg_lines.append(f'</g>')
    svg_lines.append(f'</svg>')
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_lines))
    print(f"Generated {output_file}")

if __name__ == "__main__":
    render_heatmap("data/contributions.json", "contrib-heatmap.svg")
