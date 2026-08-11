#!/usr/env/bin python3
import sys
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_contributions(username, output_file):
    url = f"https://github.com/users/{username}/contributions"
    print(f"Fetching {url}...")
    
    # Needs headers otherwise Github might serve a weird 404 or block
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Error fetching contributions: HTTP {resp.status_code}")
        sys.exit(1)
        
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Find all table cells representing days (td with class ContributionCalendar-day)
    # Note: GitHub recently updated their UI, the class is now often 'ContributionCalendar-day'
    days = soup.find_all("td", class_="ContributionCalendar-day")
    
    contributions = []
    
    for day in days:
        date_str = day.get("data-date")
        if not date_str:
            continue
            
        # Extract count - it is usually inside a tool-tip or id, but currently the easiest way is the text inside
        # Actually github puts the count in the tooltip text which we can get, or 'data-level'
        # Let's just use data-level for the color mapping. Level is 0-4.
        level = int(day.get("data-level", 0))
        
        contributions.append({
            "date": date_str,
            "level": level
        })
        
    if not contributions:
        print("Warning: Could not find any contribution data. Check if GitHub changed their HTML structure.")
        
    # Build data object
    data = {
        "username": username,
        "fetched_at": datetime.now().isoformat(),
        "contributions": contributions
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    print(f"Saved {len(contributions)} days to {output_file}")

if __name__ == "__main__":
    fetch_contributions("MdKasif0", "data/contributions.json")
