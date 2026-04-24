import httpx
from bs4 import BeautifulSoup
import json

url = "https://apps.apple.com/in/app/groww-stocks-mutual-fund-ipo/id1404871703?see-all=reviews&platform=iphone"
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
}

r = httpx.get(url, headers=headers, timeout=10.0)
soup = BeautifulSoup(r.text, "lxml")

reviews = []
# App Store reviews are typically in div with class 'we-customer-review' or similar
# Let's find them
review_divs = soup.find_all("div", class_="we-customer-review")
print(f"Found {len(review_divs)} reviews using 'we-customer-review'")

if not review_divs:
    # Try another selector
    review_divs = soup.find_all("div", class_="customer-review")
    print(f"Found {len(review_divs)} reviews using 'customer-review'")

for div in review_divs:
    title = div.find("h3", class_="we-customer-review__title")
    author = div.find("span", class_="we-customer-review__user")
    date = div.find("time")
    rating_span = div.find("figure", class_="we-star-rating")
    body = div.find("blockquote", class_="we-customer-review__body")
    
    reviews.append({
        "title": title.text.strip() if title else None,
        "author": author.text.strip() if author else None,
        "date": date.get("datetime") if date else None,
        "rating": rating_span.get("aria-label") if rating_span else None,
        "body": body.text.strip() if body else None
    })

if reviews:
    print(f"Sample review: {reviews[0]}")
else:
    # Maybe data is in a script tag?
    script_tag = soup.find("script", {"id": "shoebox-media-api-cache-amp-app"})
    if script_tag:
        print("Found data in script tag!")
