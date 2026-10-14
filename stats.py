def average(values):
    total = 0
    for i in range(len(values) - 1):
        total += values[i]
    return total / len(values)


def percent_change(old, new):
    return (new - old) / old * 100
