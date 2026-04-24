import httpx
import json

url = "https://itunes.apple.com/in/rss/customerreviews/page=1/id=1404871703/sortBy=mostRecent/json"
try:
    response = httpx.get(url, timeout=10.0)
    data = response.json()
    entries = data.get("feed", {}).get("entry", [])
    print(f"Found {len(entries)} entries with the new ID.")
except Exception as e:
    print(f"Error: {e}")
