import json
import re
from bs4 import BeautifulSoup
from agent.ingestion.models import RawReview
import hashlib
from datetime import datetime

def extract_reviews_from_html(html_content, product_key):
    soup = BeautifulSoup(html_content, "lxml")
    # Look for script tags with JSON data
    scripts = soup.find_all("script", {"type": "application/json"})
    
    all_reviews = []
    
    for script in scripts:
        try:
            data = json.loads(script.string)
            # The data structure in Apple's Shoebox can be complex.
            # We are looking for "reviews" or similar keys.
            # Based on the previous Select-String output, it seems to be in a flat structure or nested.
            
            def find_reviews(obj):
                if isinstance(obj, dict):
                    if "customerReview" in obj or "customerReviews" in obj:
                        yield obj.get("customerReview") or obj.get("customerReviews")
                    for k, v in obj.items():
                        yield from find_reviews(v)
                elif isinstance(obj, list):
                    for item in obj:
                        yield from find_reviews(item)
            
            for potential in find_reviews(data):
                if isinstance(potential, list):
                    for r in potential:
                        if isinstance(r, dict) and "body" in r:
                            # Map to RawReview
                            # r keys might be: body, date, rating, title, userName, etc.
                            body = r.get("body", "")
                            author = r.get("userName", "Anonymous")
                            date_str = r.get("date")
                            rating = r.get("rating")
                            title = r.get("title", "")
                            
                            ext_id = r.get("id") or hashlib.sha1(f"{author}{date_str}{body[:20]}".encode()).hexdigest()
                            
                            # Apple dates in Shoebox are ISO
                            try:
                                review_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                            except:
                                review_date = datetime.now()
                                
                            all_reviews.append(RawReview(
                                id=hashlib.sha1(f"appstore{ext_id}".encode()).hexdigest(),
                                product_key=product_key,
                                source="appstore",
                                external_id=str(ext_id),
                                body=f"{title}\n{body}" if title else body,
                                rating=int(rating) if rating else None,
                                review_date=review_date,
                                language="en"
                            ))
        except:
            continue
            
    return all_reviews

if __name__ == "__main__":
    with open("scratch/groww_reviews.html", "r", encoding="utf-8") as f:
        html = f.read()
    reviews = extract_reviews_from_html(html, "groww")
    print(f"Extracted {len(reviews)} reviews.")
    if reviews:
        print(f"Sample: {reviews[0]}")
