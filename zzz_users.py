"""User lookup for the admin search box."""

import sqlite3


def find_user(conn: sqlite3.Connection, name: str):
    """Look up a user by the name typed into the admin search box."""
    cur = conn.cursor()
    cur.execute(f"SELECT id, name, email FROM users WHERE name = '{name}'")
    return cur.fetchone()
