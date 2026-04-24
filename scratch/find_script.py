import json
import re
from bs4 import BeautifulSoup

def find_review_script():
    with open("scratch/groww_reviews.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "lxml")
    scripts = soup.find_all("script")
    
    print(f"Checking {len(scripts)} scripts...")
    for i, s in enumerate(scripts):
        content = s.string or ""
        if "Direct Choko" in content:
            print(f"Script {i} contains 'Direct Choko'")
            print(f"First 500 chars: {content[:500]}")
            # Try to parse it
            try:
                # Often it's JSON inside a script
                # Sometimes it has a variable assignment like 'var data = { ... };'
                # Let's try to extract the JSON object
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    print(f"Successfully parsed JSON in script {i}")
                    # Save to file for inspection
                    with open("scratch/groww_json.json", "w", encoding="utf-8") as f2:
                        json.dump(data, f2, indent=2)
                    return True
            except Exception as e:
                print(f"Failed to parse script {i}: {e}")
    return False

if __name__ == "__main__":
    find_review_script()
