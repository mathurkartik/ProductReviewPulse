import sqlite3
from pathlib import Path

DB_PATH = Path("data/pulse.db")

def check_data():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    print("--- Database Summary ---")
    
    # Check Products
    products = conn.execute("SELECT count(*) as count FROM products").fetchone()
    print(f"Products: {products['count']}")
    
    # Check Reviews
    reviews = conn.execute("SELECT count(*) as count FROM reviews").fetchone()
    print(f"Total Reviews: {reviews['count']}")
    
    # Break down by source
    sources = conn.execute("SELECT source, count(*) as count FROM reviews GROUP BY source").fetchall()
    for s in sources:
        print(f"  - {s['source']}: {s['count']}")
        
    # Check Runs
    runs = conn.execute("SELECT count(*) as count FROM runs").fetchone()
    print(f"Runs: {runs['count']}")
    
    # Latest Run Details
    latest_run = conn.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT 1").fetchone()
    if latest_run:
        print(f"\n--- Latest Run Details ---")
        print(f"Run ID: {latest_run['run_id']}")
        print(f"Product: {latest_run['product_key']}")
        print(f"Status: {latest_run['status']}")
        print(f"Created At: {latest_run['created_at']}")
        
    # Sample Review
    sample = conn.execute("SELECT * FROM reviews LIMIT 1").fetchone()
    if sample:
        print(f"\n--- Sample Review ---")
        print(f"Source: {sample['source']}")
        print(f"Rating: {sample['rating']}")
        print(f"Body: {sample['body'][:200]}...")
        
    conn.close()

if __name__ == "__main__":
    check_data()
