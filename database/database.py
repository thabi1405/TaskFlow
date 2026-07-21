import sqlite3

conn = sqlite3.connect("database/taskflow.db")

cursor = conn.cursor()

# Users Table

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")

# Tasks Table

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    due_date TEXT,
    priority TEXT,
    completed INTEGER DEFAULT 0,

    FOREIGN KEY(user_id)
    REFERENCES users(id)
)
""")

conn.commit()
conn.close()

print("Database created successfully.")