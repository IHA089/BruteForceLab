import sqlite3
import random
import hashlib


def create_database():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gmail TEXT NOT NULL,
        username TEXT NOT NULL,
        password TEXT NOT NULL
    )
    ''')

    numb = random.randint(100, 999)
    passw = "admin@"+str(numb)
    passw_hash = hashlib.md5(passw.encode()).hexdigest()
    query = "INSERT INTO users (gmail, username, password) VALUES ('admin@iha089.org', 'admin', '"+passw_hash+"')"

    cursor.execute(query)

    conn.commit()
    conn.close()
