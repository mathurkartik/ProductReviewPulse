import sqlite3
conn = sqlite3.connect('data/pulse.db')
conn.execute("UPDATE runs SET status='clustered' WHERE run_id='f6c8e2b797aad2f7e45a56e8745b04852d9850b8'")
conn.execute("DELETE FROM themes WHERE run_id='f6c8e2b797aad2f7e45a56e8745b04852d9850b8'")
conn.commit()
print("Reset Groww run to 'clustered'")
