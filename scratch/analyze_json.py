import json

def find_keys(obj, target):
    if isinstance(obj, dict):
        if target in obj:
            yield obj[target]
        for k, v in obj.items():
            yield from find_keys(v, target)
    elif isinstance(obj, list):
        for item in obj:
            yield from find_keys(item, target)

with open('scratch/groww_json.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

reviews = list(find_keys(data, 'userReview'))
print(f"Found {len(reviews)} reviews.")

if reviews:
    r = reviews[0]
    print("Keys:", r.keys())
    # Often it has attributes like 'body', 'rating', 'title', 'userName', 'date'
    print("Sample:", {k: v for k, v in r.items() if k in ['body', 'rating', 'title', 'userName', 'date']})
