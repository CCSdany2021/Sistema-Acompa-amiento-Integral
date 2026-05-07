import sqlite3

conn = sqlite3.connect("data/db/acompanamiento.db")
cursor = conn.cursor()
cursor.execute("SELECT id, email, role, assigned_section FROM users LIMIT 3")
for row in cursor.fetchall():
    print(row)
conn.close()
