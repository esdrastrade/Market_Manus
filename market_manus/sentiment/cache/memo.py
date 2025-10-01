from cachetools import TTLCache

cache = TTLCache(maxsize=512, ttl=60)

def get(key):
    return cache.get(key)

def put(key, value):
    cache[key] = value
