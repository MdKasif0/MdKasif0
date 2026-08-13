#!/usr/env/bin python3
import sys
import json
import requests
import os
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_contributions(username, output_file):
    url = f"https://github.com/users/{username}/contributions"
    print(f"Fetching {url}...")
    resp = requests.get(url)
    if resp.status_code != 200:
        print(f"Failed to fetch contributions: HTTP {resp.status_code}")
        return

    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Github heatmap is a table of elements containing data-date and data-level
    days = []
    for td in soup.find_all('td', {'data-date': True}):
        date = td.get('data-date')
        level = td.get('data-level', '0')
        days.append({
            'date': date,
            'level': int(level)
        })
        
    print(f"Parsed {len(days)} days of contributions.")
    
    dirname = os.path.dirname(output_file)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(days, f, indent=2)

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "data/contributions.json"
    fetch_contributions("MdKasif0", out_file)
