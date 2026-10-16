def average(values):
    if not values:
        raise ValueError("average() requires a non-empty list")
    return sum(values) / len(values)


def percent_change(old, new):
    return (new - old) / old * 100
