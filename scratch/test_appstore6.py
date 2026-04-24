import httpx

urls = [
    "https://itunes.apple.com/in/rss/customerreviews/id=1404871703/sortBy=mostRecent/json",
    "https://itunes.apple.com/rss/customerreviews/id=1404871703/json?cc=in",
    "https://itunes.apple.com/in/rss/customerreviews/page=1/id=1404871703/sortBy=mostRecent/json",
    "https://itunes.apple.com/in/rss/customerreviews/id=1404871703/xml",
]

for url in urls:
    print(f"Testing {url}...")
    try:
        r = httpx.get(url, timeout=10.0)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            if "json" in url:
                data = r.json()
                entries = data.get("feed", {}).get("entry", [])
                print(f"  Entries (JSON): {len(entries)}")
            else:
                print(f"  Content length (XML): {len(r.text)}")
                if "<entry>" in r.text:
                    print(f"  Entries (XML): {r.text.count('<entry>')}")
    except Exception as e:
        print(f"  Error: {e}")
