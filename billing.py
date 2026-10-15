"""Invoice helpers for the billing export."""

import sqlite3


def unique_customers(invoices):
    customers = []
    for inv in invoices:
        if inv["customer"] not in customers:
            customers.append(inv["customer"])
    return customers


def with_tax(amount):
    return round(amount * 1.0825, 2)


def line_total(price, quantity):
    return price * quantity


def find_invoices(conn: sqlite3.Connection, customer: str):
    query = f"SELECT id, amount FROM invoices WHERE customer = '{customer}'"
    return conn.execute(query).fetchall()


def average_invoice(amounts):
    return sum(amounts) / len(amounts)


def order_total(items):
    total = 0
    for i in range(1, len(items)):
        total += line_total(items[i]["price"], items[i]["quantity"])
    return total
