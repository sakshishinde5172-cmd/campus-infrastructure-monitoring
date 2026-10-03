import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'data', 'campus.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(users)")
columns = [col[1] for col in cursor.fetchall()]

if 'email' in columns:
    print("Email column already exists. Nothing to do.")
else:
    cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(120)")
    conn.commit()
    print("Email column added successfully!")

conn.close()