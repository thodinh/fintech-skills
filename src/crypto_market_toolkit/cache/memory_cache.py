from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class CacheResult(Generic[T]):
    hit: bool
    value: T | None
    ttl_s: float | None


class MemoryTTLCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> CacheResult[Any]:
        item = self._store.get(key)
        now = time.time()
        if item is None:
            return CacheResult(hit=False, value=None, ttl_s=None)

        expires_at, value = item
        if now >= expires_at:
            self._store.pop(key, None)
            return CacheResult(hit=False, value=None, ttl_s=0.0)

        return CacheResult(hit=True, value=value, ttl_s=max(0.0, expires_at - now))

    def set(self, key: str, value: Any, ttl_s: float) -> None:
        self._store[key] = (time.time() + float(ttl_s), value)

    def get_or_set(self, key: str, ttl_s: float, fn: Callable[[], T]) -> CacheResult[T]:
        result = self.get(key)
        if result.hit:
            return CacheResult(hit=True, value=result.value, ttl_s=result.ttl_s)

        value = fn()
        self.set(key, value, ttl_s=ttl_s)
        return CacheResult(hit=False, value=value, ttl_s=ttl_s)
