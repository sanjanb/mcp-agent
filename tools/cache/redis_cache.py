import json
import os
from typing import Any, Optional

try:
    import redis
except Exception: 
    redis = None


class _InMemoryCache:
    def __init__(self):
        self._store = {}

    def get_json(self, key: str) -> Optional[Any]:
        val = self._store.get(key)
        if val is None:
            return None
        try:
            return json.loads(val)
        except Exception:
            return None

    def set_json(self, key: str, value: Any):
        self._store[key] = json.dumps(value)

    def set_json_ttl(self, key: str, value: Any, ttl_seconds: int):
        # TTL ignored in memory fallback
        self.set_json(key, value)

    def delete(self, key: str):
        self._store.pop(key, None)


class RedisCache:
    def __init__(self, client):
        self.client = client

    def get_json(self, key: str) -> Optional[Any]:
        raw = self.client.get(key)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    def set_json(self, key: str, value: Any):
        self.client.set(key, json.dumps(value))

    def set_json_ttl(self, key: str, value: Any, ttl_seconds: int):
        self.client.setex(key, ttl_seconds, json.dumps(value))

    def delete(self, key: str):
        self.client.delete(key)


def get_cache():
    """Create a Redis-backed cache if available, else in-memory fallback."""
    url = os.getenv("REDIS_URL")
    if redis is None:
        return _InMemoryCache()
    try:
        if url:
            client = redis.Redis.from_url(url)
        else:
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", "6379"))
            db = int(os.getenv("REDIS_DB", "0"))
            client = redis.Redis(host=host, port=port, db=db)
        # health check
        client.ping()
        return RedisCache(client)
    except Exception:
        return _InMemoryCache()
