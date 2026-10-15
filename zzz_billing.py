import sqlite3


def find_invoices(conn: sqlite3.Connection, customer: str):
    query = f"SELECT * FROM invoices WHERE customer = '{customer}'"
    return conn.execute(query).fetchall()


def percent_change(old: float, new: float) -> float:
    return (new - old) / old * 100


def calculate(expression: str) -> float:
    allowed = {"add_tax": 1.0825}
    if expression not in allowed:
        raise ValueError(f"unknown calculation: {expression}")
    return allowed[expression]
