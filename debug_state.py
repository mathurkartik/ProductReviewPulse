import sqlite3
from pathlib import Path

print("=== Checking pulse.sqlite ===")
if Path("pulse.sqlite").exists():
    conn = sqlite3.connect("pulse.sqlite")
    conn.row_factory = sqlite3.Row
    
    run = conn.execute("SELECT id, product_key, iso_week, status FROM runs ORDER BY updated_at DESC LIMIT 1").fetchone()
    if run:
        print(f"Latest run: {run['id'][:16]}... | Status: {run['status']}")
    else:
        print("No runs found")
    
    themes = conn.execute("SELECT COUNT(*) as count FROM themes").fetchone()
    print(f"Themes: {themes['count']}")
    conn.close()
else:
    print("pulse.sqlite not found")

print("\n=== Checking Files ===")
for p in ["data/summaries", "data/artifacts", "data/raw"]:
    path = Path(p)
    if path.exists():
        files = list(path.iterdir())
        print(f"{p}: {len(files)} files")
        for f in files[:3]:
            print(f"  - {f.name}")
    else:
        print(f"{p}: not found")

print("\n=== Checking pulse.sqlite (root) ===")
if Path("pulse.sqlite").exists():
    conn = sqlite3.connect("pulse.sqlite")
    conn.row_factory = sqlite3.Row
    run = conn.execute("SELECT run_id, status FROM runs ORDER BY updated_at DESC LIMIT 1").fetchone()
    if run:
        print(f"Latest run: {run['run_id'][:16]}... | Status: {run['status']}")
    conn.close()
else:
    print("pulse.sqlite not found")
