def retry_delay(attempt):
    d = 0.5
    for i in range(attempt):
        d = d * 2
    if d > 30:
        d = 30
    return d
