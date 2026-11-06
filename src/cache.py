import time

_CACHE = {}


def get_user(uid, fetch):
    hit = _CACHE.get(uid)
    if hit and time.time() - hit[0] < 60:
        return hit[1]
    user = fetch(uid)
    _CACHE[uid] = (time.time(), user)
    return user
