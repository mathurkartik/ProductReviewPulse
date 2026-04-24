import httpx

url = "https://itunes.apple.com/in/rss/customerreviews/page=1/id=1404871703/sortBy=mostRecent/json"
r = httpx.get(url, timeout=10.0)
print(r.status_code)
print(r.text[:1000])
