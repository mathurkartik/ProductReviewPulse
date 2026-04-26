import sqlite3
conn = sqlite3.connect('data/pulse.db')
conn.execute("UPDATE runs SET status='rendered'")
conn.commit()
print("Successfully reset run status to 'rendered'!")
