"""Helpers for splitting work into even and odd batches."""


def is_even(n):
    """Return True if n is even."""
    return n % 2 == 0


def split_batches(ids):
    """Return (even_ids, odd_ids)."""
    even = [i for i in ids if is_even(i)]
    odd = [i for i in ids if not is_even(i)]
    return even, odd
