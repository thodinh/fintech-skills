from __future__ import annotations

import time
from typing import Any

from finance_market_skills.cache.memory_cache import MemoryTTLCache
from finance_market_skills.exchanges.registry import create_exchange

DEFAULT_QUOTE_WHITELIST = ["USDT", "USDC", "BTC", "ETH"]


def normalize_symbol(
    symbol: str, quote_whitelist: list[str] | None = None
) -> tuple[str, list[str]]:
    s = symbol.strip()
    if "/" in s:
        return s, []

    whitelist = quote_whitelist or DEFAULT_QUOTE_WHITELIST
    for quote in whitelist:
        upper_s = s.upper()
        if upper_s.endswith(quote) and len(upper_s) > len(quote):
            base = upper_s[: -len(quote)]
            normalized = f"{base}/{quote}"
            warning = f"symbol_heuristic=compact_pair({symbol}->{normalized})"
            return normalized, [warning]

    return s, [f"symbol_warning=unrecognized_format({symbol})"]


def _sleep_backoff(attempt: int) -> None:
    time.sleep(min(2.0, 0.25 * (2**attempt)))


class ExchangeClient:
    def __init__(self, exchange: str, *, market_type: str = "spot", timeout_ms: int = 15000) -> None:
        self.exchange_name = exchange
        self.market_type = market_type
        self.timeout_ms = timeout_ms
        self._ex = create_exchange(exchange, market_type=market_type, timeout_ms=timeout_ms)
        self._cache = MemoryTTLCache()

    @property
    def id(self) -> str:
        return getattr(self._ex, "id", self.exchange_name)

    def load_markets_cached(self, ttl_s: float = 1800.0) -> dict[str, Any]:
        key = f"load_markets:{self.id}"
        result = self._cache.get_or_set(key, ttl_s, lambda: self._ex.load_markets())
        return result.value or {}

    def call_cached(
        self,
        *,
        cache_key: str,
        ttl_s: float,
        method: str,
        args: list[Any],
        kwargs: dict[str, Any] | None = None,
        max_retries: int = 2,
    ) -> tuple[Any, dict[str, Any]]:
        kwargs = kwargs or {}
        cache_result = self._cache.get(cache_key)
        if cache_result.hit:
            return cache_result.value, {"cache": {"hit": True, "ttl_s": cache_result.ttl_s}}

        last_err: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                fn = getattr(self._ex, method)
                value = fn(*args, **kwargs)
                self._cache.set(cache_key, value, ttl_s=ttl_s)
                return value, {"cache": {"hit": False, "ttl_s": ttl_s}}
            except Exception as exc:
                last_err = exc
                if attempt >= max_retries:
                    break
                _sleep_backoff(attempt)

        raise RuntimeError(str(last_err)) from last_err
