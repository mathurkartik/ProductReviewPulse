import json

def find_reviews(obj):
    if isinstance(obj, dict):
        if obj.get("$kind") == "Review":
            yield obj
        for v in obj.values():
            yield from find_reviews(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from find_reviews(item)

with open('scratch/groww_json.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

reviews = list(find_reviews(data))
print(f"Found {len(reviews)} reviews.")

if reviews:
    print(f"Sample: {reviews[0]}")
