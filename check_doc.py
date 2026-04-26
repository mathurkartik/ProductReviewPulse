import sqlite3

conn = sqlite3.connect("pulse.sqlite")
conn.row_factory = sqlite3.Row

# Check product gdoc_id
p = conn.execute("SELECT key, display, gdoc_id FROM products WHERE key='groww'").fetchone()
if p:
    print(f"Product: {p['display']}")
    print(f"GDoc ID: {p['gdoc_id'] or 'Not set'}")
else:
    print("Product 'groww' not found")

# Check run status
r = conn.execute("SELECT id, status, gdoc_heading_id, gmail_message_id FROM runs ORDER BY updated_at DESC LIMIT 1").fetchone()
if r:
    print(f"\nLatest Run: {r['id'][:16]}...")
    print(f"Status: {r['status']}")
    print(f"GDoc Heading ID: {r['gdoc_heading_id'] or 'Not set'}")
    print(f"Gmail Message ID: {r['gmail_message_id'] or 'Not set'}")

conn.close()
