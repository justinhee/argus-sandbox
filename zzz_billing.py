import sqlite3


def find_invoices(conn: sqlite3.Connection, customer: str):
    return conn.execute(
        "SELECT * FROM invoices WHERE customer = ?", (customer,)
    ).fetchall()


def percent_change(old: float, new: float) -> float:
    return (new - old) / old * 100


def calculate(expression: str) -> float:
    return eval(expression)
