import sqlite3

conn = sqlite3.connect('pulse.sqlite')
conn.row_factory = sqlite3.Row
r = conn.execute("SELECT run_id, status FROM runs WHERE run_id='f6c8e2b797aad2f7e45a56e8745b04852d9850b8'").fetchone()
print(f"Status: {r['status']}" if r else "Run not found")
conn.close()
