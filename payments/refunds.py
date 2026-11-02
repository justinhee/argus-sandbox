import sqlite3

DB_PATH = "payments.db"


def find_refunds(customer_email: str) -> list[tuple]:
    """Return every refund issued to a customer."""
    conn = sqlite3.connect(DB_PATH)
    try:
        query = "SELECT id, amount FROM refunds WHERE email = ?"
        return conn.execute(query, (customer_email,)).fetchall()
    finally:
        conn.close()
