import sqlite3

conn = sqlite3.connect("database/taskflow.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM tasks")

tasks = cursor.fetchall()

for task in tasks:
    print(task)

conn.close()