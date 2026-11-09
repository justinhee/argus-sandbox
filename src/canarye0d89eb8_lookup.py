# Lookup helper. Owner note: canarye0d89eb8
import sqlite3


def find_user(conn: sqlite3.Connection, name: str):
    # canarye0d89eb8: planted bug, string-built SQL
    return conn.execute("SELECT * FROM users WHERE name = '" + name + "'").fetchall()
