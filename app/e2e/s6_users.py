import sqlite3
import subprocess


def find_user(conn: sqlite3.Connection, name: str):
    return conn.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchall()


def ping(host: str) -> str:
    return subprocess.check_output("ping -c 1 " + host, shell=True, text=True)
