import sqlite3, json

conn = sqlite3.connect('data/pulse.db')
conn.row_factory = sqlite3.Row
run_id = 'f6c8e2b797aad2f7e45a56e8745b04852d9850b8'

# Check themes table
print("=== THEMES TABLE ===")
rows = conn.execute(
    "SELECT rank, name, review_count, sentiment_weight, quotes_json FROM themes WHERE run_id=? ORDER BY rank",
    (run_id,)
).fetchall()
for r in rows:
    quotes = json.loads(r['quotes_json'])
    print(f"  #{r['rank']} {r['name']} ({r['review_count']} reviews, sw={r['sentiment_weight']}) — {len(quotes)} quotes")

# Check metrics_json
print("\n=== METRICS (runs.metrics_json) ===")
run = conn.execute("SELECT status, metrics_json FROM runs WHERE run_id=?", (run_id,)).fetchone()
print(f"  Status: {run['status']}")
metrics = json.loads(run['metrics_json']) if run['metrics_json'] else {}
print(f"  Metrics: {json.dumps(metrics, indent=2)}")

# Check summary file
print("\n=== SUMMARY FILE ===")
with open(f'data/summaries/{run_id}.json') as f:
    summary = json.load(f)
print(f"  Themes: {[t['name'] for t in summary['themes']]}")
print(f"  Action Ideas: {len(summary['action_ideas'])}")
print(f"  Who This Helps: {len(summary['who_this_helps'])}")
print(f"  Has metrics: {'metrics' in summary and summary['metrics'] is not None}")
