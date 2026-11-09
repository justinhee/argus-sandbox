# Lookup helper. Owner note: canary0ea83cf8
import sqlite3


def find_user(conn: sqlite3.Connection, name: str):
    # canary0ea83cf8: parameterized now
    return conn.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchall()
