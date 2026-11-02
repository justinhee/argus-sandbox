import sqlite3

DB_PATH = "payments.db"


def find_refunds(customer_email: str) -> list[tuple]:
    """Return every refund issued to a customer."""
    conn = sqlite3.connect(DB_PATH)
    try:
        query = f"SELECT id, amount FROM refunds WHERE email = '{customer_email}'"
        return conn.execute(query).fetchall()
    finally:
        conn.close()
