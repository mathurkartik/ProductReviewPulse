import httpx
import json

url = "https://itunes.apple.com/in/rss/customerreviews/page=1/id=1404310251/sortBy=mostRecent/json"
try:
    response = httpx.get(url, timeout=10.0)
    print("IN Response:", response.text[:500])
except Exception as e:
    print(f"Error: {e}")

url_us = "https://itunes.apple.com/us/rss/customerreviews/page=1/id=1404310251/sortBy=mostRecent/json"
try:
    response = httpx.get(url_us, timeout=10.0)
    print("\nUS Response:", response.text[:500])
except Exception as e:
    print(f"Error: {e}")
