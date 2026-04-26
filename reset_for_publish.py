import sqlite3

conn = sqlite3.connect('data/pulse.db')
conn.row_factory = sqlite3.Row

# Update run status to 'rendered' so we can re-publish
conn.execute("UPDATE runs SET status = 'rendered' WHERE id = 'f6c8e2b797aad2f7e45a56e8745b04852d9850b8'")
conn.commit()

# Clear gdoc_id to force new doc creation
conn.execute("UPDATE products SET gdoc_id = NULL WHERE key = 'groww'")
conn.commit()

print('Reset run status to rendered, cleared gdoc_id')
conn.close()
