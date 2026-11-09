# Lookup helper. Owner note: canary0ea83cf8
import sqlite3


def find_user(conn: sqlite3.Connection, name: str):
    # canary0ea83cf8: planted bug, string-built SQL
    return conn.execute("SELECT * FROM users WHERE name = '" + name + "'").fetchall()
