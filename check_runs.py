import sqlite3
from pathlib import Path

DB_PATH = Path("pulse.sqlite")

def check_runs():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    print("=== Recent Runs ===")
    runs = conn.execute(
        "SELECT run_id, product_key, iso_week, status, updated_at FROM runs ORDER BY updated_at DESC LIMIT 5"
    ).fetchall()
    
    for r in runs:
        print(f"Run: {r['run_id'][:16]}... | Product: {r['product_key']} | Week: {r['iso_week']} | Status: {r['status']}")
    
    # Check if any run needs clustering
    pending = conn.execute("SELECT COUNT(*) as count FROM runs WHERE status = 'ingested'").fetchone()
    clustered = conn.execute("SELECT COUNT(*) as count FROM runs WHERE status = 'clustered'").fetchone()
    summarized = conn.execute("SELECT COUNT(*) as count FROM runs WHERE status = 'summarized'").fetchone()
    rendered = conn.execute("SELECT COUNT(*) as count FROM runs WHERE status = 'rendered'").fetchone()
    
    print(f"\n=== Pipeline Status ===")
    print(f"Ingested:   {pending['count']} (needs clustering)")
    print(f"Clustered:  {clustered['count']} (needs summarization)")
    print(f"Summarized: {summarized['count']} (needs rendering)")
    print(f"Rendered:   {rendered['count']} (ready to publish)")
    
    # Check themes count
    themes = conn.execute("SELECT COUNT(*) as count FROM themes").fetchone()
    print(f"\nTotal themes generated: {themes['count']}")
    
    conn.close()

if __name__ == "__main__":
    check_runs()
