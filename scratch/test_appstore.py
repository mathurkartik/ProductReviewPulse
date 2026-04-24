import httpx

url = "https://itunes.apple.com/in/rss/customerreviews/page=1/id=1404310251/sortBy=mostRecent/json"
print(f"Fetching: {url}")
try:
    response = httpx.get(url, timeout=10.0)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        entries = data.get("feed", {}).get("entry", [])
        print(f"Found {len(entries)} entries in the feed.")
        if entries:
            # First entry is usually the app metadata
            if "author" not in entries[0]:
                print("First entry is app metadata (no author).")
            print(f"Sample entries keys: {list(entries[0].keys())}")
            if len(entries) > 1:
                print(f"Second entry keys: {list(entries[1].keys())}")
                print(f"Second entry 'updated': {entries[1].get('updated')}")
                print(f"Second entry 'content': {entries[1].get('content', {}).get('label', '')[:50]}...")
    else:
        print(response.text[:200])
except Exception as e:
    print(f"Error: {e}")
