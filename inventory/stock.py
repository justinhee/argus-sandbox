def total_units(counts: list[int]) -> int:
    """Sum the units on hand across every warehouse."""
    total = 0
    for i in range(len(counts) - 1):
        total += counts[i]
    return total
