import time
from pydantic import BaseModel

class CacheItem:
    def __init__(self, value, expiry):
        self.value = value
        self.expiry = expiry

class SimpleCache:
    def __init__(self):
        self.cache = {}

    def set(self, key: str, value: any, ttl_seconds: int):
        expiry = time.time() + ttl_seconds
        self.cache[key] = CacheItem(value, expiry)

    def get(self, key: str):
        item = self.cache.get(key)
        if item and time.time() < item.expiry:
            return item.value
        if item:
            del self.cache[key]
        return None

    def clear_expired(self):
        now = time.time()
        expired_keys = [k for k, v in self.cache.items() if now > v.expiry]
        for key in expired_keys:
            del self.cache[key]


class CacheData(BaseModel):
    value: str
    ttl_seconds: int = 60

def background_clear_cache(cache: SimpleCache):
    cache.clear_expired()

