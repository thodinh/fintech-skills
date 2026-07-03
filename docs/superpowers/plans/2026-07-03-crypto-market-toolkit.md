# Crypto Market Toolkit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a Python Skill-like toolkit powered by `ccxt` that provides AI-agent friendly tools for crypto market data, indicators, and market scanners (market data only).

**Architecture:** A small Python package with a ccxt client wrapper (rate-limit, retry, symbol normalization), an in-memory TTL cache, modular market-data and indicator functions, and scanner utilities. All tools return a standardized JSON-friendly response envelope with `summary` and `highlights`.

**Tech Stack:** Python 3.11+, `ccxt`, `pytest` (tests). Standard library for indicator math (no pandas dependency in MVP).

---

## Repo structure (to be created)

- `pyproject.toml`
- `src/crypto_market_toolkit/__init__.py`
- `src/crypto_market_toolkit/schemas/response.py`
- `src/crypto_market_toolkit/cache/memory_cache.py`
- `src/crypto_market_toolkit/exchanges/registry.py`
- `src/crypto_market_toolkit/exchanges/client.py`
- `src/crypto_market_toolkit/market_data/price.py`
- `src/crypto_market_toolkit/market_data/ticker.py`
- `src/crypto_market_toolkit/market_data/ohlcv.py`
- `src/crypto_market_toolkit/market_data/orderbook.py`
- `src/crypto_market_toolkit/market_data/trades.py`
- `src/crypto_market_toolkit/indicators/moving_averages.py`
- `src/crypto_market_toolkit/indicators/rsi.py`
- `src/crypto_market_toolkit/indicators/macd.py`
- `src/crypto_market_toolkit/indicators/bbands.py`
- `src/crypto_market_toolkit/indicators/atr.py`
- `src/crypto_market_toolkit/indicators/vwap.py`
- `src/crypto_market_toolkit/indicators/compute.py`
- `src/crypto_market_toolkit/scanners/top_movers.py`
- `src/crypto_market_toolkit/scanners/volume_spikes.py`
- `src/crypto_market_toolkit/scanners/volatility_rank.py`
- `src/crypto_market_toolkit/scanners/breakouts.py`
- `tests/test_response_schema.py`
- `tests/test_indicators_rsi.py`
- `tests/test_indicators_macd.py`
- `tests/test_indicators_bbands.py`
- `tests/test_indicators_atr.py`
- `tests/test_indicators_vwap.py`
- `tests/test_symbol_normalization.py`

---

### Task 1: Initialize Python package (pyproject + src layout)

**Files:**
- Create: `/workspace/pyproject.toml`
- Create: `/workspace/src/crypto_market_toolkit/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "crypto-market-toolkit"
version = "0.1.0"
description = "AI-agent friendly crypto market data + indicators toolkit using ccxt"
requires-python = ">=3.11"
dependencies = [
  "ccxt>=4.0.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 2: Create package init**

```python
__all__ = [
    "get_price",
    "get_ticker",
    "get_ohlcv",
    "get_orderbook",
    "get_trades",
    "compute_indicators",
    "scan_top_movers",
    "scan_volume_spikes",
    "scan_volatility_rank",
    "scan_breakouts",
]
```

- [ ] **Step 3: Install deps (editable)**

Run:

```bash
python -m pip install -e ".[dev]"
```

Expected: installs `ccxt` and `pytest` without errors.

---

### Task 2: Implement response envelope + helpers

**Files:**
- Create: `/workspace/src/crypto_market_toolkit/schemas/response.py`
- Create: `/workspace/tests/test_response_schema.py`

- [ ] **Step 1: Write failing test for envelope fields**

```python
from crypto_market_toolkit.schemas.response import ok_response, error_response


def test_ok_response_has_required_fields():
    r = ok_response(
        query={"exchange": "binance", "symbol": "BTC/USDT", "market_type": "spot"},
        data={"x": 1},
        stats={"y": 2},
        summary="ok",
        highlights=["x=1"],
        meta={"exchange_id": "binance"},
    )
    assert r["ok"] is True
    assert "summary" in r and isinstance(r["summary"], str)
    assert "highlights" in r and isinstance(r["highlights"], list)
    assert "query" in r and isinstance(r["query"], dict)
    assert "data" in r and isinstance(r["data"], dict)
    assert "stats" in r and isinstance(r["stats"], dict)
    assert "meta" in r and isinstance(r["meta"], dict)
    assert r["error"] is None


def test_error_response_has_required_fields():
    r = error_response(
        query={"exchange": "binance", "symbol": "BAD", "market_type": "spot"},
        code="INVALID_SYMBOL",
        message="bad symbol",
        context={"method": "fetch_ticker", "retryable": False},
    )
    assert r["ok"] is False
    assert r["error"]["code"] == "INVALID_SYMBOL"
    assert r["error"]["context"]["retryable"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest -q
```

Expected: FAIL because `crypto_market_toolkit.schemas.response` does not exist.

- [ ] **Step 3: Implement `ok_response` / `error_response`**

```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now() -> tuple[int, str]:
    ts_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    iso_time = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()
    return ts_ms, iso_time


def ok_response(
    *,
    query: Dict[str, Any],
    data: Dict[str, Any],
    stats: Optional[Dict[str, Any]] = None,
    summary: str,
    highlights: List[str],
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ts_ms, iso_time = _now()
    return {
        "ok": True,
        "summary": summary,
        "highlights": highlights,
        "query": query,
        "ts_ms": ts_ms,
        "iso_time": iso_time,
        "data": data,
        "stats": stats or {},
        "meta": meta or {},
        "error": None,
    }


def error_response(
    *,
    query: Dict[str, Any],
    code: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ts_ms, iso_time = _now()
    return {
        "ok": False,
        "summary": message,
        "highlights": [f"error_code={code}"],
        "query": query,
        "ts_ms": ts_ms,
        "iso_time": iso_time,
        "data": {},
        "stats": {},
        "meta": meta or {},
        "error": {
            "code": code,
            "message": message,
            "context": context or {"method": None, "retryable": False},
        },
    }
```

- [ ] **Step 4: Run tests**

Run:

```bash
pytest -q
```

Expected: PASS for `test_response_schema.py`.

---

### Task 3: Add TTL in-memory cache

**Files:**
- Create: `/workspace/src/crypto_market_toolkit/cache/memory_cache.py`

- [ ] **Step 1: Implement `MemoryTTLCache`**

```python
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, Optional, Tuple, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class CacheResult(Generic[T]):
    hit: bool
    value: Optional[T]
    ttl_s: Optional[float]


class MemoryTTLCache:
    def __init__(self) -> None:
        self._store: Dict[str, Tuple[float, Any]] = {}

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
        r = self.get(key)
        if r.hit:
            return CacheResult(hit=True, value=r.value, ttl_s=r.ttl_s)
        value = fn()
        self.set(key, value, ttl_s=ttl_s)
        return CacheResult(hit=False, value=value, ttl_s=ttl_s)
```

---

### Task 4: Exchange registry + client wrapper (rate limit, timeout, retry, symbol normalize)

**Files:**
- Create: `/workspace/src/crypto_market_toolkit/exchanges/registry.py`
- Create: `/workspace/src/crypto_market_toolkit/exchanges/client.py`
- Create: `/workspace/tests/test_symbol_normalization.py`

- [ ] **Step 1: Add exchange registry**

```python
from __future__ import annotations

from typing import Any, Dict

import ccxt


SUPPORTED_EXCHANGES: Dict[str, str] = {
    "binance": "binance",
    "bybit": "bybit",
    "okx": "okx",
}


def create_exchange(exchange: str, *, market_type: str = "spot", timeout_ms: int = 15000) -> Any:
    ex_id = SUPPORTED_EXCHANGES.get(exchange.lower())
    if not ex_id:
        raise ValueError(f"Unsupported exchange: {exchange}")
    cls = getattr(ccxt, ex_id)
    options: Dict[str, Any] = {}
    if market_type in {"spot", "swap", "future"}:
        options["defaultType"] = market_type
    return cls(
        {
            "enableRateLimit": True,
            "timeout": timeout_ms,
            "options": options,
        }
    )
```

- [ ] **Step 2: Add normalization helper test**

```python
from crypto_market_toolkit.exchanges.client import normalize_symbol


def test_normalize_symbol_passthrough():
    assert normalize_symbol("BTC/USDT") == ("BTC/USDT", [])


def test_normalize_symbol_compact_pair():
    sym, warnings = normalize_symbol("BTCUSDT")
    assert sym == "BTC/USDT"
    assert warnings
```

- [ ] **Step 3: Implement client wrapper (including normalize_symbol)**

```python
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from crypto_market_toolkit.cache.memory_cache import MemoryTTLCache
from crypto_market_toolkit.exchanges.registry import create_exchange


DEFAULT_QUOTE_WHITELIST = ["USDT", "USDC", "BTC", "ETH"]


def normalize_symbol(symbol: str, quote_whitelist: Optional[List[str]] = None) -> Tuple[str, List[str]]:
    s = symbol.strip()
    if "/" in s:
        return s, []
    wl = quote_whitelist or DEFAULT_QUOTE_WHITELIST
    for q in wl:
        if s.upper().endswith(q) and len(s) > len(q):
            base = s.upper()[: -len(q)]
            return f"{base}/{q}", [f"symbol_heuristic=compact_pair({symbol}->{base}/{q})"]
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

    def load_markets_cached(self, ttl_s: float = 1800.0) -> Dict[str, Any]:
        key = f"load_markets:{self.id}"
        r = self._cache.get_or_set(key, ttl_s, lambda: self._ex.load_markets())
        return r.value or {}

    def call_cached(
        self,
        *,
        cache_key: str,
        ttl_s: float,
        method: str,
        args: List[Any],
        kwargs: Optional[Dict[str, Any]] = None,
        max_retries: int = 2,
    ) -> Tuple[Any, Dict[str, Any]]:
        kwargs = kwargs or {}
        cache_r = self._cache.get(cache_key)
        if cache_r.hit:
            return cache_r.value, {"cache": {"hit": True, "ttl_s": cache_r.ttl_s}}

        last_err: Optional[Exception] = None
        for attempt in range(max_retries + 1):
            try:
                fn = getattr(self._ex, method)
                value = fn(*args, **kwargs)
                self._cache.set(cache_key, value, ttl_s=ttl_s)
                return value, {"cache": {"hit": False, "ttl_s": ttl_s}}
            except Exception as e:
                last_err = e
                if attempt >= max_retries:
                    break
                _sleep_backoff(attempt)
        raise RuntimeError(str(last_err)) from last_err
```

- [ ] **Step 4: Run tests**

Run:

```bash
pytest -q
```

Expected: PASS (offline tests only).

---

### Task 5: Implement market data tools (price/ticker/ohlcv/orderbook/trades)

**Files:**
- Create: `/workspace/src/crypto_market_toolkit/market_data/price.py`
- Create: `/workspace/src/crypto_market_toolkit/market_data/ticker.py`
- Create: `/workspace/src/crypto_market_toolkit/market_data/ohlcv.py`
- Create: `/workspace/src/crypto_market_toolkit/market_data/orderbook.py`
- Create: `/workspace/src/crypto_market_toolkit/market_data/trades.py`
- Modify: `/workspace/src/crypto_market_toolkit/__init__.py` (wire exports)

- [ ] **Step 1: Implement `get_ticker` (core pattern)**

Create: `/workspace/src/crypto_market_toolkit/market_data/ticker.py`

```python
from __future__ import annotations

from typing import Any, Dict, Optional

from crypto_market_toolkit.exchanges.client import ExchangeClient, normalize_symbol
from crypto_market_toolkit.schemas.response import error_response, ok_response


def get_ticker(
    exchange: str,
    symbol: str,
    *,
    market_type: str = "spot",
    ttl_s: float = 3.0,
    timeout_ms: int = 15000,
) -> Dict[str, Any]:
    q = {
        "exchange": exchange,
        "symbol": symbol,
        "market_type": market_type,
        "timeframe": None,
        "since_ms": None,
        "limit": None,
        "params": {},
    }
    try:
        if market_type not in {"spot", "swap", "future"}:
            return error_response(
                query=q,
                code="UNSUPPORTED_MARKET_TYPE",
                message=f"Unsupported market_type: {market_type}",
                context={"method": "fetch_ticker", "retryable": False},
            )

        client = ExchangeClient(exchange, market_type=market_type, timeout_ms=timeout_ms)
        norm_symbol, warnings = normalize_symbol(symbol)
        client.load_markets_cached()

        raw, cache_meta = client.call_cached(
            cache_key=f"ticker:{client.id}:{market_type}:{norm_symbol}",
            ttl_s=ttl_s,
            method="fetch_ticker",
            args=[norm_symbol],
        )

        last = raw.get("last")
        bid = raw.get("bid")
        ask = raw.get("ask")
        spread_abs = (ask - bid) if (isinstance(ask, (int, float)) and isinstance(bid, (int, float))) else None
        spread_pct = ((spread_abs / ((ask + bid) / 2)) * 100) if (spread_abs is not None and (ask + bid) != 0) else None

        data = {
            "last": last,
            "bid": bid,
            "ask": ask,
            "open": raw.get("open"),
            "high": raw.get("high"),
            "low": raw.get("low"),
            "base_volume": raw.get("baseVolume"),
            "quote_volume": raw.get("quoteVolume"),
            "change": raw.get("change"),
            "percentage": raw.get("percentage"),
            "ts_ms": raw.get("timestamp"),
        }
        stats = {
            "spread_abs": spread_abs,
            "spread_pct": spread_pct,
            "range_pct": (
                ((data["high"] - data["low"]) / ((bid + ask) / 2) * 100)
                if all(isinstance(x, (int, float)) for x in [data.get("high"), data.get("low"), bid, ask]) and (bid + ask) != 0
                else None
            ),
        }
        summary = f"{norm_symbol} ({exchange} {market_type}) last={last} pct_24h={data.get('percentage')}"
        highlights = [
            f"symbol={norm_symbol}",
            f"last={last}",
            f"pct_24h={data.get('percentage')}",
            f"spread_pct={spread_pct}",
        ]
        meta = {
            "source": "ccxt",
            "exchange_id": client.id,
            "rate_limit_enabled": True,
            "timeout_ms": timeout_ms,
            "cache": cache_meta["cache"],
            "units": {"price": "quote", "volume": "base", "ts": "ms"},
            "precision": {"price_decimals": None, "amount_decimals": None},
            "warnings": warnings,
        }
        q["symbol"] = norm_symbol
        return ok_response(query=q, data=data, stats=stats, summary=summary, highlights=highlights, meta=meta)
    except Exception as e:
        return error_response(
            query=q,
            code="UPSTREAM_ERROR",
            message=str(e),
            context={"method": "fetch_ticker", "retryable": True},
        )
```

- [ ] **Step 2: Create `get_price`**

Create: `/workspace/src/crypto_market_toolkit/market_data/price.py`

```python
from __future__ import annotations

from typing import Any, Dict

from crypto_market_toolkit.market_data.ticker import get_ticker
from crypto_market_toolkit.schemas.response import error_response, ok_response


def get_price(
    exchange: str,
    symbol: str,
    *,
    market_type: str = "spot",
    ttl_s: float = 3.0,
    timeout_ms: int = 15000,
) -> Dict[str, Any]:
    r = get_ticker(exchange, symbol, market_type=market_type, ttl_s=ttl_s, timeout_ms=timeout_ms)
    if not r.get("ok"):
        return r
    data = {"last": r["data"].get("last"), "ts_ms": r["data"].get("ts_ms")}
    stats = {
        "bid": r["data"].get("bid"),
        "ask": r["data"].get("ask"),
        "spread_abs": r["stats"].get("spread_abs"),
        "spread_pct": r["stats"].get("spread_pct"),
    }
    summary = f"{r['query']['symbol']} ({exchange} {market_type}) last={data['last']}"
    highlights = [
        f"symbol={r['query']['symbol']}",
        f"last={data['last']}",
        f"spread_pct={stats.get('spread_pct')}",
    ]
    meta = r.get("meta", {})
    meta["cache"] = r.get("meta", {}).get("cache", {})
    return ok_response(query=r["query"], data=data, stats=stats, summary=summary, highlights=highlights, meta=meta)
```

- [ ] **Step 3: Create `get_ohlcv`**

Create: `/workspace/src/crypto_market_toolkit/market_data/ohlcv.py`

```python
from __future__ import annotations

import math
import statistics
from typing import Any, Dict, List, Optional, Tuple

from crypto_market_toolkit.exchanges.client import ExchangeClient, normalize_symbol
from crypto_market_toolkit.schemas.response import error_response, ok_response


def _tail(arr: List[Any], n: int) -> List[Any]:
    if n <= 0:
        return []
    return arr[-n:] if len(arr) > n else arr


def _log_returns(closes: List[float]) -> List[float]:
    out: List[float] = []
    for i in range(1, len(closes)):
        a = closes[i - 1]
        b = closes[i]
        if a and b and a > 0 and b > 0:
            out.append(math.log(b / a))
    return out


def get_ohlcv(
    exchange: str,
    symbol: str,
    *,
    timeframe: str = "1m",
    limit: int = 500,
    since_ms: Optional[int] = None,
    market_type: str = "spot",
    full_series: bool = False,
    series_tail_size: int = 120,
    ttl_s: float = 20.0,
    timeout_ms: int = 15000,
) -> Dict[str, Any]:
    q = {
        "exchange": exchange,
        "symbol": symbol,
        "market_type": market_type,
        "timeframe": timeframe,
        "since_ms": since_ms,
        "limit": limit,
        "params": {
            "full_series": full_series,
            "series_tail_size": series_tail_size,
        },
    }
    try:
        if market_type not in {"spot", "swap", "future"}:
            return error_response(
                query=q,
                code="UNSUPPORTED_MARKET_TYPE",
                message=f"Unsupported market_type: {market_type}",
                context={"method": "fetch_ohlcv", "retryable": False},
            )

        client = ExchangeClient(exchange, market_type=market_type, timeout_ms=timeout_ms)
        norm_symbol, warnings = normalize_symbol(symbol)
        client.load_markets_cached()

        raw, cache_meta = client.call_cached(
            cache_key=f"ohlcv:{client.id}:{market_type}:{norm_symbol}:{timeframe}:{since_ms}:{limit}",
            ttl_s=ttl_s,
            method="fetch_ohlcv",
            args=[norm_symbol, timeframe, since_ms, limit],
        )

        ohlcv_full: List[List[Any]] = raw or []
        ohlcv_tail = _tail(ohlcv_full, series_tail_size)
        ohlcv = ohlcv_full if full_series else ohlcv_tail
        closes_tail: List[float] = [float(c[4]) for c in ohlcv_tail if c and len(c) >= 5 and isinstance(c[4], (int, float))]

        return_pct = None
        if len(closes_tail) >= 2 and closes_tail[0] != 0:
            return_pct = (closes_tail[-1] / closes_tail[0] - 1) * 100

        lrs = _log_returns(closes_tail)
        volatility = statistics.pstdev(lrs) if len(lrs) >= 2 else None

        ranges_pct: List[float] = []
        vols: List[float] = []
        for c in ohlcv_tail:
            if not c or len(c) < 6:
                continue
            o, h, l, cl, v = c[1], c[2], c[3], c[4], c[5]
            if isinstance(h, (int, float)) and isinstance(l, (int, float)) and isinstance(cl, (int, float)) and cl:
                ranges_pct.append(((h - l) / cl) * 100)
            if isinstance(v, (int, float)):
                vols.append(float(v))

        stats = {
            "return_pct": return_pct,
            "volatility": volatility,
            "avg_range_pct": (sum(ranges_pct) / len(ranges_pct)) if ranges_pct else None,
            "avg_volume": (sum(vols) / len(vols)) if vols else None,
        }

        data = {
            "ohlcv": ohlcv,
            "ohlcv_tail": ohlcv_tail,
            "last_candle": ohlcv_tail[-1] if ohlcv_tail else None,
            "series_full_truncated": (not full_series) and (len(ohlcv_full) > len(ohlcv_tail)),
            "series_tail_size": series_tail_size,
        }

        last_close = closes_tail[-1] if closes_tail else None
        summary = f"{norm_symbol} ({exchange} {market_type}) ohlcv {timeframe} last_close={last_close} return_pct={return_pct}"
        highlights = [
            f"symbol={norm_symbol}",
            f"timeframe={timeframe}",
            f"last_close={last_close}",
            f"return_pct={return_pct}",
            f"volatility={volatility}",
        ]
        meta = {
            "source": "ccxt",
            "exchange_id": client.id,
            "rate_limit_enabled": True,
            "timeout_ms": timeout_ms,
            "cache": cache_meta["cache"],
            "units": {"price": "quote", "volume": "base", "ts": "ms"},
            "precision": {"price_decimals": None, "amount_decimals": None},
            "warnings": warnings,
        }
        q["symbol"] = norm_symbol
        return ok_response(query=q, data=data, stats=stats, summary=summary, highlights=highlights, meta=meta)
    except Exception as e:
        return error_response(
            query=q,
            code="UPSTREAM_ERROR",
            message=str(e),
            context={"method": "fetch_ohlcv", "retryable": True},
        )
```

- [ ] **Step 4: Create `get_orderbook`**

Create: `/workspace/src/crypto_market_toolkit/market_data/orderbook.py`

```python
from __future__ import annotations

from typing import Any, Dict

from crypto_market_toolkit.exchanges.client import ExchangeClient, normalize_symbol
from crypto_market_toolkit.schemas.response import error_response, ok_response


def _depth_notional(levels, max_levels: int = 50) -> float:
    total = 0.0
    for p, a in (levels or [])[:max_levels]:
        if isinstance(p, (int, float)) and isinstance(a, (int, float)):
            total += float(p) * float(a)
    return total


def get_orderbook(
    exchange: str,
    symbol: str,
    *,
    limit: int = 100,
    market_type: str = "spot",
    ttl_s: float = 2.0,
    timeout_ms: int = 15000,
) -> Dict[str, Any]:
    q = {
        "exchange": exchange,
        "symbol": symbol,
        "market_type": market_type,
        "timeframe": None,
        "since_ms": None,
        "limit": limit,
        "params": {},
    }
    try:
        client = ExchangeClient(exchange, market_type=market_type, timeout_ms=timeout_ms)
        norm_symbol, warnings = normalize_symbol(symbol)
        client.load_markets_cached()

        raw, cache_meta = client.call_cached(
            cache_key=f"orderbook:{client.id}:{market_type}:{norm_symbol}:{limit}",
            ttl_s=ttl_s,
            method="fetch_order_book",
            args=[norm_symbol, limit],
        )

        bids = raw.get("bids") or []
        asks = raw.get("asks") or []
        best_bid = bids[0][0] if bids else None
        best_ask = asks[0][0] if asks else None
        spread_abs = (best_ask - best_bid) if isinstance(best_ask, (int, float)) and isinstance(best_bid, (int, float)) else None
        spread_pct = (
            (spread_abs / ((best_ask + best_bid) / 2)) * 100
            if spread_abs is not None and (best_ask + best_bid) != 0
            else None
        )

        data = {"bids": bids, "asks": asks, "ts_ms": raw.get("timestamp")}
        stats = {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread_abs": spread_abs,
            "spread_pct": spread_pct,
            "depth_bid_notional": _depth_notional(bids),
            "depth_ask_notional": _depth_notional(asks),
        }
        summary = f"{norm_symbol} ({exchange} {market_type}) spread_pct={spread_pct} bid={best_bid} ask={best_ask}"
        highlights = [
            f"symbol={norm_symbol}",
            f"spread_pct={spread_pct}",
            f"best_bid={best_bid}",
            f"best_ask={best_ask}",
        ]
        meta = {
            "source": "ccxt",
            "exchange_id": client.id,
            "rate_limit_enabled": True,
            "timeout_ms": timeout_ms,
            "cache": cache_meta["cache"],
            "units": {"price": "quote", "volume": "base", "ts": "ms"},
            "precision": {"price_decimals": None, "amount_decimals": None},
            "warnings": warnings,
        }
        q["symbol"] = norm_symbol
        return ok_response(query=q, data=data, stats=stats, summary=summary, highlights=highlights, meta=meta)
    except Exception as e:
        return error_response(
            query=q,
            code="UPSTREAM_ERROR",
            message=str(e),
            context={"method": "fetch_order_book", "retryable": True},
        )
```

- [ ] **Step 5: Create `get_trades`**

Create: `/workspace/src/crypto_market_toolkit/market_data/trades.py`

```python
from __future__ import annotations

from typing import Any, Dict, List, Optional

from crypto_market_toolkit.exchanges.client import ExchangeClient, normalize_symbol
from crypto_market_toolkit.schemas.response import error_response, ok_response


def get_trades(
    exchange: str,
    symbol: str,
    *,
    limit: int = 200,
    since_ms: Optional[int] = None,
    market_type: str = "spot",
    ttl_s: float = 3.0,
    timeout_ms: int = 15000,
) -> Dict[str, Any]:
    q = {
        "exchange": exchange,
        "symbol": symbol,
        "market_type": market_type,
        "timeframe": None,
        "since_ms": since_ms,
        "limit": limit,
        "params": {},
    }
    try:
        client = ExchangeClient(exchange, market_type=market_type, timeout_ms=timeout_ms)
        norm_symbol, warnings = normalize_symbol(symbol)
        client.load_markets_cached()

        raw, cache_meta = client.call_cached(
            cache_key=f"trades:{client.id}:{market_type}:{norm_symbol}:{since_ms}:{limit}",
            ttl_s=ttl_s,
            method="fetch_trades",
            args=[norm_symbol, since_ms, limit],
        )

        trades: List[Dict[str, Any]] = []
        buy_volume = 0.0
        sell_volume = 0.0
        for t in raw or []:
            ts = t.get("timestamp")
            price = t.get("price")
            amount = t.get("amount")
            side = t.get("side")
            trades.append({"ts_ms": ts, "price": price, "amount": amount, "side": side})
            if isinstance(amount, (int, float)):
                if side == "buy":
                    buy_volume += float(amount)
                elif side == "sell":
                    sell_volume += float(amount)

        ratio = (buy_volume / sell_volume) if sell_volume else None
        data = {"trades": trades, "ts_ms": None}
        stats = {"buy_volume": buy_volume, "sell_volume": sell_volume, "buy_sell_ratio": ratio}
        summary = f"{norm_symbol} ({exchange} {market_type}) trades={len(trades)} buy_sell_ratio={ratio}"
        highlights = [
            f"symbol={norm_symbol}",
            f"trades_count={len(trades)}",
            f"buy_volume={buy_volume}",
            f"sell_volume={sell_volume}",
        ]
        meta = {
            "source": "ccxt",
            "exchange_id": client.id,
            "rate_limit_enabled": True,
            "timeout_ms": timeout_ms,
            "cache": cache_meta["cache"],
            "units": {"price": "quote", "volume": "base", "ts": "ms"},
            "precision": {"price_decimals": None, "amount_decimals": None},
            "warnings": warnings,
        }
        q["symbol"] = norm_symbol
        return ok_response(query=q, data=data, stats=stats, summary=summary, highlights=highlights, meta=meta)
    except Exception as e:
        return error_response(
            query=q,
            code="UPSTREAM_ERROR",
            message=str(e),
            context={"method": "fetch_trades", "retryable": True},
        )
```

- [ ] **Step 3: Update `__init__.py` to re-export tool functions**

```python
from crypto_market_toolkit.market_data.price import get_price
from crypto_market_toolkit.market_data.ticker import get_ticker
from crypto_market_toolkit.market_data.ohlcv import get_ohlcv
from crypto_market_toolkit.market_data.orderbook import get_orderbook
from crypto_market_toolkit.market_data.trades import get_trades
from crypto_market_toolkit.indicators.compute import compute_indicators
from crypto_market_toolkit.scanners.top_movers import scan_top_movers
from crypto_market_toolkit.scanners.volume_spikes import scan_volume_spikes
from crypto_market_toolkit.scanners.volatility_rank import scan_volatility_rank
from crypto_market_toolkit.scanners.breakouts import scan_breakouts
```

- [ ] **Step 4: Run lint-free smoke import**

Run:

```bash
python -c "import crypto_market_toolkit as c; print(sorted(c.__all__))"
```

Expected: prints exported tool names.

---

### Task 6: Implement indicator math with unit tests (offline)

**Files:**
- Create: `/workspace/src/crypto_market_toolkit/indicators/*`
- Create: `/workspace/tests/test_indicators_*.py`

- [ ] **Step 1: Create moving averages helpers (SMA/EMA)**

```python
from __future__ import annotations

from typing import List, Optional


def sma_series(values: List[float], period: int) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(values)
    if period <= 0:
        return out
    s = 0.0
    for i, v in enumerate(values):
        s += float(v)
        if i >= period:
            s -= float(values[i - period])
        if i >= period - 1:
            out[i] = s / period
    return out


def ema_series(values: List[float], period: int) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(values)
    if period <= 0 or not values:
        return out
    k = 2.0 / (period + 1.0)
    ema: Optional[float] = None
    for i, v in enumerate(values):
        fv = float(v)
        if ema is None:
            ema = fv
        else:
            ema = (fv - ema) * k + ema
        out[i] = ema
    return out
```

Create: `/workspace/src/crypto_market_toolkit/indicators/moving_averages.py` with the code above.

- [ ] **Step 2: Create RSI + unit test**

Create: `/workspace/src/crypto_market_toolkit/indicators/rsi.py`

```python
from __future__ import annotations

from typing import List, Optional


def rsi_series(closes: List[float], period: int = 14) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(closes)
    if period <= 0 or len(closes) < 2:
        return out

    gains: List[float] = [0.0] * len(closes)
    losses: List[float] = [0.0] * len(closes)
    for i in range(1, len(closes)):
        d = float(closes[i]) - float(closes[i - 1])
        gains[i] = d if d > 0 else 0.0
        losses[i] = -d if d < 0 else 0.0

    avg_gain = sum(gains[1 : period + 1]) / period
    avg_loss = sum(losses[1 : period + 1]) / period
    if avg_loss == 0:
        out[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        out[period] = 100.0 - (100.0 / (1.0 + rs))

    for i in range(period + 1, len(closes)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            out[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            out[i] = 100.0 - (100.0 / (1.0 + rs))
    return out
```

Create: `/workspace/tests/test_indicators_rsi.py`

```python
from crypto_market_toolkit.indicators.rsi import rsi_series


def test_rsi_series_length_matches_input():
    closes = [1, 2, 3, 2, 2, 4, 3, 5, 6, 7, 6, 6, 7, 8, 9, 10]
    out = rsi_series(closes, period=14)
    assert len(out) == len(closes)
    assert out[-1] is not None
```

---

- [ ] **Step 3: Create MACD + unit test**

Create: `/workspace/src/crypto_market_toolkit/indicators/macd.py`

```python
from __future__ import annotations

from typing import List, Optional, Tuple

from crypto_market_toolkit.indicators.moving_averages import ema_series


def macd_series(
    closes: List[float], *, fast: int = 12, slow: int = 26, signal: int = 9
) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    ema_fast = ema_series(closes, fast)
    ema_slow = ema_series(closes, slow)
    macd: List[Optional[float]] = [None] * len(closes)
    for i in range(len(closes)):
        a = ema_fast[i]
        b = ema_slow[i]
        macd[i] = (a - b) if (a is not None and b is not None) else None

    macd_vals = [m if m is not None else 0.0 for m in macd]
    sig = ema_series(macd_vals, signal)
    hist: List[Optional[float]] = [None] * len(closes)
    for i in range(len(closes)):
        m = macd[i]
        s = sig[i]
        hist[i] = (m - s) if (m is not None and s is not None) else None
    return macd, sig, hist
```

Create: `/workspace/tests/test_indicators_macd.py`

```python
from crypto_market_toolkit.indicators.macd import macd_series


def test_macd_shapes():
    closes = list(range(1, 200))
    macd, signal, hist = macd_series(closes, fast=12, slow=26, signal=9)
    assert len(macd) == len(signal) == len(hist) == len(closes)
```

- [ ] **Step 4: Create Bollinger Bands + unit test**

Create: `/workspace/src/crypto_market_toolkit/indicators/bbands.py`

```python
from __future__ import annotations

import statistics
from typing import List, Optional, Tuple


def bbands_series(
    closes: List[float], *, period: int = 20, stddev: float = 2.0
) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    mid: List[Optional[float]] = [None] * len(closes)
    upper: List[Optional[float]] = [None] * len(closes)
    lower: List[Optional[float]] = [None] * len(closes)
    if period <= 0:
        return mid, upper, lower

    for i in range(len(closes)):
        if i < period - 1:
            continue
        window = [float(x) for x in closes[i - period + 1 : i + 1]]
        m = sum(window) / period
        sd = statistics.pstdev(window) if len(window) >= 2 else 0.0
        mid[i] = m
        upper[i] = m + stddev * sd
        lower[i] = m - stddev * sd
    return mid, upper, lower
```

Create: `/workspace/tests/test_indicators_bbands.py`

```python
from crypto_market_toolkit.indicators.bbands import bbands_series


def test_bbands_length():
    closes = list(range(1, 100))
    mid, upper, lower = bbands_series(closes, period=20, stddev=2.0)
    assert len(mid) == len(upper) == len(lower) == len(closes)
```

- [ ] **Step 5: Create ATR + unit test**

Create: `/workspace/src/crypto_market_toolkit/indicators/atr.py`

```python
from __future__ import annotations

from typing import List, Optional


def atr_series(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> List[Optional[float]]:
    n = len(closes)
    out: List[Optional[float]] = [None] * n
    if period <= 0 or n == 0:
        return out

    tr: List[float] = [0.0] * n
    for i in range(n):
        h = float(highs[i])
        l = float(lows[i])
        if i == 0:
            tr[i] = h - l
        else:
            pc = float(closes[i - 1])
            tr[i] = max(h - l, abs(h - pc), abs(l - pc))

    if n < period:
        return out

    atr = sum(tr[:period]) / period
    out[period - 1] = atr
    for i in range(period, n):
        atr = (atr * (period - 1) + tr[i]) / period
        out[i] = atr
    return out
```

Create: `/workspace/tests/test_indicators_atr.py`

```python
from crypto_market_toolkit.indicators.atr import atr_series


def test_atr_length():
    highs = [10, 11, 12, 13, 12, 12, 14]
    lows = [9, 9, 10, 11, 10, 11, 12]
    closes = [9.5, 10, 11, 12, 11.5, 11.8, 13]
    out = atr_series(highs, lows, closes, period=3)
    assert len(out) == len(closes)
```

- [ ] **Step 6: Create VWAP + unit test**

Create: `/workspace/src/crypto_market_toolkit/indicators/vwap.py`

```python
from __future__ import annotations

from typing import List, Optional


def vwap_series(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    volumes: List[float],
    *,
    window: Optional[int] = None,
) -> List[Optional[float]]:
    n = len(closes)
    out: List[Optional[float]] = [None] * n
    if n == 0:
        return out

    cum_pv = 0.0
    cum_v = 0.0
    pv_hist: List[float] = []
    v_hist: List[float] = []
    for i in range(n):
        tp = (float(highs[i]) + float(lows[i]) + float(closes[i])) / 3.0
        v = float(volumes[i])
        pv = tp * v
        pv_hist.append(pv)
        v_hist.append(v)
        cum_pv += pv
        cum_v += v

        if window is not None and window > 0 and i >= window:
            cum_pv -= pv_hist[i - window]
            cum_v -= v_hist[i - window]

        out[i] = (cum_pv / cum_v) if cum_v else None
    return out
```

Create: `/workspace/tests/test_indicators_vwap.py`

```python
from crypto_market_toolkit.indicators.vwap import vwap_series


def test_vwap_length():
    highs = [10, 11, 12]
    lows = [9, 10, 11]
    closes = [9.5, 10.5, 11.5]
    vols = [100, 200, 150]
    out = vwap_series(highs, lows, closes, vols, window=None)
    assert len(out) == len(closes)
```

- [ ] **Step 7: Run tests**

Run:

```bash
pytest -q
```

Expected: PASS (no network).

---

### Task 7: Implement `compute_indicators` orchestration (tool)

**Files:**
- Create: `/workspace/src/crypto_market_toolkit/indicators/compute.py`

- [ ] **Step 1: Implement `compute_indicators`**

```python
from __future__ import annotations

from typing import Any, Dict, List, Optional

from crypto_market_toolkit.indicators.atr import atr_series
from crypto_market_toolkit.indicators.bbands import bbands_series
from crypto_market_toolkit.indicators.macd import macd_series
from crypto_market_toolkit.indicators.moving_averages import ema_series, sma_series
from crypto_market_toolkit.indicators.rsi import rsi_series
from crypto_market_toolkit.indicators.vwap import vwap_series
from crypto_market_toolkit.market_data.ohlcv import get_ohlcv
from crypto_market_toolkit.schemas.response import error_response, ok_response


def _signal_rsi(last: Optional[float]) -> Optional[str]:
    if last is None:
        return None
    if last < 30:
        return "rsi_state=oversold"
    if last > 70:
        return "rsi_state=overbought"
    return "rsi_state=neutral"


def _signal_macd(hist: List[Optional[float]]) -> Optional[str]:
    if len(hist) < 2:
        return None
    a = hist[-2]
    b = hist[-1]
    if a is None or b is None:
        return None
    if a <= 0 and b > 0:
        return "macd_cross_up"
    if a >= 0 and b < 0:
        return "macd_cross_down"
    return None


def _signal_bbands(close: Optional[float], upper: Optional[float], lower: Optional[float]) -> Optional[str]:
    if close is None or upper is None or lower is None:
        return None
    if close >= upper:
        return "bb_position=upper_zone"
    if close <= lower:
        return "bb_position=lower_zone"
    return "bb_position=mid_zone"


def compute_indicators(
    exchange: str,
    symbol: str,
    *,
    timeframe: str = "1h",
    limit: int = 500,
    since_ms: Optional[int] = None,
    market_type: str = "spot",
    indicators: Optional[List[str]] = None,
    indicator_params: Optional[Dict[str, Any]] = None,
    full_series: bool = False,
    series_tail_size: int = 120,
    timeout_ms: int = 15000,
) -> Dict[str, Any]:
    indicators = indicators or ["rsi", "macd", "bbands"]
    indicator_params = indicator_params or {}

    q = {
        "exchange": exchange,
        "symbol": symbol,
        "market_type": market_type,
        "timeframe": timeframe,
        "since_ms": since_ms,
        "limit": limit,
        "params": {
            "indicators": indicators,
            "indicator_params": indicator_params,
            "full_series": full_series,
            "series_tail_size": series_tail_size,
        },
    }

    o = get_ohlcv(
        exchange,
        symbol,
        timeframe=timeframe,
        limit=limit,
        since_ms=since_ms,
        market_type=market_type,
        full_series=full_series,
        series_tail_size=series_tail_size,
        timeout_ms=timeout_ms,
    )
    if not o.get("ok"):
        return o

    ohlcv_tail = o["data"].get("ohlcv_tail") or []
    if not ohlcv_tail:
        return error_response(
            query=q,
            code="UPSTREAM_ERROR",
            message="No OHLCV returned",
            context={"method": "fetch_ohlcv", "retryable": True},
        )

    highs = [float(c[2]) for c in ohlcv_tail]
    lows = [float(c[3]) for c in ohlcv_tail]
    closes = [float(c[4]) for c in ohlcv_tail]
    volumes = [float(c[5]) for c in ohlcv_tail]

    out: Dict[str, Any] = {}
    signals: List[str] = []

    for name in indicators:
        if name.startswith("sma"):
            period = int(indicator_params.get(name, {}).get("period", 20))
            s = sma_series(closes, period)
            out[name] = {"params": {"period": period}, "series_tail": s, "last": s[-1], "signal": None}
        elif name.startswith("ema"):
            period = int(indicator_params.get(name, {}).get("period", 20))
            s = ema_series(closes, period)
            out[name] = {"params": {"period": period}, "series_tail": s, "last": s[-1], "signal": None}
        elif name == "rsi":
            period = int(indicator_params.get("rsi", {}).get("period", 14))
            s = rsi_series(closes, period=period)
            sig = _signal_rsi(s[-1])
            out["rsi"] = {"params": {"period": period}, "series_tail": s, "last": s[-1], "signal": sig}
            if sig:
                signals.append(sig)
        elif name == "macd":
            p = indicator_params.get("macd", {})
            fast = int(p.get("fast", 12))
            slow = int(p.get("slow", 26))
            signal = int(p.get("signal", 9))
            macd, sig_line, hist = macd_series(closes, fast=fast, slow=slow, signal=signal)
            sig = _signal_macd(hist)
            out["macd"] = {
                "params": {"fast": fast, "slow": slow, "signal": signal},
                "series_tail": {"macd": macd, "signal": sig_line, "hist": hist},
                "last": {"macd": macd[-1], "signal": sig_line[-1], "hist": hist[-1]},
                "signal": sig,
            }
            if sig:
                signals.append(sig)
        elif name == "bbands":
            p = indicator_params.get("bbands", {})
            period = int(p.get("period", 20))
            stddev = float(p.get("stddev", 2.0))
            mid, upper, lower = bbands_series(closes, period=period, stddev=stddev)
            sig = _signal_bbands(closes[-1], upper[-1], lower[-1])
            out["bbands"] = {
                "params": {"period": period, "stddev": stddev},
                "series_tail": {"mid": mid, "upper": upper, "lower": lower},
                "last": {"mid": mid[-1], "upper": upper[-1], "lower": lower[-1]},
                "signal": sig,
            }
            if sig:
                signals.append(sig)
        elif name == "atr":
            period = int(indicator_params.get("atr", {}).get("period", 14))
            s = atr_series(highs, lows, closes, period=period)
            out["atr"] = {"params": {"period": period}, "series_tail": s, "last": s[-1], "signal": None}
        elif name == "vwap":
            p = indicator_params.get("vwap", {})
            window = p.get("window", None)
            win = int(window) if window is not None else None
            s = vwap_series(highs, lows, closes, volumes, window=win)
            out["vwap"] = {"params": {"window": win}, "series_tail": s, "last": s[-1], "signal": None}

    last_close = closes[-1] if closes else None
    summary = f"{o['query']['symbol']} ({exchange} {market_type}) {timeframe} close={last_close} signals={','.join(signals) if signals else 'none'}"
    highlights = [
        f"symbol={o['query']['symbol']}",
        f"timeframe={timeframe}",
        f"close_last={last_close}",
    ] + signals[:3]

    data = {"ohlcv_tail": ohlcv_tail, "indicators": out}
    stats = {"close_last": last_close, "return_pct_tail": o["stats"].get("return_pct"), "volatility": o["stats"].get("volatility")}
    meta = o.get("meta", {})
    return ok_response(query=o["query"], data=data, stats=stats, summary=summary, highlights=highlights, meta=meta)
```

- [ ] **Step 2: Run smoke call (online optional)**

Run:

```bash
python -c "from crypto_market_toolkit import compute_indicators; print(compute_indicators('binance','BTC/USDT',timeframe='1h',limit=200,indicators=['rsi','macd','bbands'])['ok'])"
```

Expected: `True` if network allowed; if not, expect `ok=False` with `UPSTREAM_ERROR`.

---

### Task 8: Implement scanners (top movers, spikes, volatility, breakouts)

**Files:**
- Create: `/workspace/src/crypto_market_toolkit/scanners/top_movers.py`
- Create: `/workspace/src/crypto_market_toolkit/scanners/volume_spikes.py`
- Create: `/workspace/src/crypto_market_toolkit/scanners/volatility_rank.py`
- Create: `/workspace/src/crypto_market_toolkit/scanners/breakouts.py`

- [ ] **Step 1: Implement `scan_top_movers`**

```python
from __future__ import annotations

from typing import Any, Dict, List, Optional

from crypto_market_toolkit.exchanges.client import ExchangeClient
from crypto_market_toolkit.schemas.response import error_response, ok_response


def scan_top_movers(
    exchange: str,
    *,
    quote: str = "USDT",
    market_type: str = "spot",
    top_n: int = 20,
    max_symbols: int = 200,
    timeout_ms: int = 15000,
) -> Dict[str, Any]:
    q = {
        "exchange": exchange,
        "symbol": None,
        "market_type": market_type,
        "timeframe": "24h",
        "since_ms": None,
        "limit": top_n,
        "params": {"quote": quote, "max_symbols": max_symbols},
    }
    try:
        client = ExchangeClient(exchange, market_type=market_type, timeout_ms=timeout_ms)
        markets = client.load_markets_cached()
        symbols = [s for s, m in markets.items() if isinstance(s, str) and s.endswith(f"/{quote}")]
        symbols = symbols[:max_symbols]

        results: List[Dict[str, Any]] = []
        for sym in symbols:
            raw, _ = client.call_cached(
                cache_key=f"ticker:{client.id}:{market_type}:{sym}",
                ttl_s=3.0,
                method="fetch_ticker",
                args=[sym],
            )
            pct = raw.get("percentage")
            qv = raw.get("quoteVolume")
            results.append(
                {
                    "symbol": sym,
                    "metrics": {"pct_24h": pct, "quote_volume": qv, "last": raw.get("last")},
                    "reason": f"pct_24h={pct} quote_volume={qv}",
                }
            )

        results.sort(key=lambda x: (x["metrics"]["pct_24h"] is not None, x["metrics"]["pct_24h"]), reverse=True)
        top = results[:top_n]
        summary = f"{exchange} movers quote={quote} top_n={top_n} universe={len(symbols)}"
        highlights = [f"exchange={exchange}", f"quote={quote}", f"top_n={top_n}", f"universe={len(symbols)}"]
        meta = {
            "source": "ccxt",
            "exchange_id": client.id,
            "rate_limit_enabled": True,
            "timeout_ms": timeout_ms,
            "cache": {"hit": False, "ttl_s": None},
            "units": {"price": "quote", "volume": "base", "ts": "ms"},
            "precision": {"price_decimals": None, "amount_decimals": None},
            "warnings": [],
        }
        return ok_response(query=q, data={"results": top}, stats={}, summary=summary, highlights=highlights, meta=meta)
    except Exception as e:
        return error_response(
            query=q,
            code="UPSTREAM_ERROR",
            message=str(e),
            context={"method": "fetch_ticker", "retryable": True},
        )
```

Create: `/workspace/src/crypto_market_toolkit/scanners/top_movers.py` with the code above.

- [ ] **Step 2: Implement `scan_volume_spikes`**

```python
from __future__ import annotations

from typing import Any, Dict, List, Optional

from crypto_market_toolkit.exchanges.client import ExchangeClient
from crypto_market_toolkit.market_data.ohlcv import get_ohlcv
from crypto_market_toolkit.schemas.response import error_response, ok_response


def scan_volume_spikes(
    exchange: str,
    *,
    quote: str = "USDT",
    timeframe: str = "1h",
    lookback: int = 48,
    spike_factor: float = 3.0,
    top_n: int = 20,
    max_symbols: int = 200,
    market_type: str = "spot",
    timeout_ms: int = 15000,
) -> Dict[str, Any]:
    q = {
        "exchange": exchange,
        "symbol": None,
        "market_type": market_type,
        "timeframe": timeframe,
        "since_ms": None,
        "limit": top_n,
        "params": {"quote": quote, "lookback": lookback, "spike_factor": spike_factor, "max_symbols": max_symbols},
    }
    try:
        client = ExchangeClient(exchange, market_type=market_type, timeout_ms=timeout_ms)
        markets = client.load_markets_cached()
        symbols = [s for s in markets.keys() if isinstance(s, str) and s.endswith(f"/{quote}")]
        symbols = symbols[:max_symbols]

        results: List[Dict[str, Any]] = []
        for sym in symbols:
            o = get_ohlcv(
                exchange,
                sym,
                timeframe=timeframe,
                limit=max(lookback, 10),
                market_type=market_type,
                series_tail_size=max(lookback, 10),
                timeout_ms=timeout_ms,
            )
            if not o.get("ok"):
                continue
            tail = o["data"].get("ohlcv_tail") or []
            vols = [float(c[5]) for c in tail if c and len(c) >= 6]
            if len(vols) < 2:
                continue
            last_v = vols[-1]
            base = vols[-lookback:] if len(vols) >= lookback else vols
            avg_v = (sum(base) / len(base)) if base else 0.0
            spike = (last_v / avg_v) if avg_v else None
            if spike is None or spike < spike_factor:
                continue
            results.append(
                {
                    "symbol": sym,
                    "metrics": {"spike": spike, "volume_last": last_v, "avg_volume": avg_v},
                    "reason": f"volume_spike={spike}x last={last_v} avg={avg_v}",
                }
            )

        results.sort(key=lambda x: x["metrics"]["spike"], reverse=True)
        top = results[:top_n]
        summary = f"{exchange} volume spikes quote={quote} timeframe={timeframe} found={len(top)}"
        highlights = [f"exchange={exchange}", f"timeframe={timeframe}", f"found={len(top)}", f"spike_factor={spike_factor}"]
        meta = {
            "source": "ccxt",
            "exchange_id": client.id,
            "rate_limit_enabled": True,
            "timeout_ms": timeout_ms,
            "cache": {"hit": False, "ttl_s": None},
            "units": {"price": "quote", "volume": "base", "ts": "ms"},
            "precision": {"price_decimals": None, "amount_decimals": None},
            "warnings": [],
        }
        return ok_response(query=q, data={"results": top}, stats={}, summary=summary, highlights=highlights, meta=meta)
    except Exception as e:
        return error_response(
            query=q,
            code="UPSTREAM_ERROR",
            message=str(e),
            context={"method": "fetch_ohlcv", "retryable": True},
        )
```

Create: `/workspace/src/crypto_market_toolkit/scanners/volume_spikes.py` with the code above.

- [ ] **Step 3: Implement `scan_volatility_rank`**

```python
from __future__ import annotations

import math
import statistics
from typing import Any, Dict, List

from crypto_market_toolkit.exchanges.client import ExchangeClient
from crypto_market_toolkit.market_data.ohlcv import get_ohlcv
from crypto_market_toolkit.schemas.response import error_response, ok_response


def scan_volatility_rank(
    exchange: str,
    *,
    quote: str = "USDT",
    timeframe: str = "1h",
    lookback: int = 120,
    top_n: int = 20,
    max_symbols: int = 200,
    market_type: str = "spot",
    timeout_ms: int = 15000,
) -> Dict[str, Any]:
    q = {
        "exchange": exchange,
        "symbol": None,
        "market_type": market_type,
        "timeframe": timeframe,
        "since_ms": None,
        "limit": top_n,
        "params": {"quote": quote, "lookback": lookback, "max_symbols": max_symbols},
    }
    try:
        client = ExchangeClient(exchange, market_type=market_type, timeout_ms=timeout_ms)
        markets = client.load_markets_cached()
        symbols = [s for s in markets.keys() if isinstance(s, str) and s.endswith(f"/{quote}")]
        symbols = symbols[:max_symbols]

        results: List[Dict[str, Any]] = []
        for sym in symbols:
            o = get_ohlcv(
                exchange,
                sym,
                timeframe=timeframe,
                limit=max(lookback, 20),
                market_type=market_type,
                series_tail_size=max(lookback, 20),
                timeout_ms=timeout_ms,
            )
            if not o.get("ok"):
                continue
            tail = o["data"].get("ohlcv_tail") or []
            closes = [float(c[4]) for c in tail if c and len(c) >= 5]
            if len(closes) < 3:
                continue
            lrs = []
            for i in range(1, len(closes)):
                a = closes[i - 1]
                b = closes[i]
                if a > 0 and b > 0:
                    lrs.append(math.log(b / a))
            vol = statistics.pstdev(lrs) if len(lrs) >= 2 else 0.0
            results.append({"symbol": sym, "metrics": {"volatility": vol}, "reason": f"volatility={vol}"})

        results.sort(key=lambda x: x["metrics"]["volatility"], reverse=True)
        top = results[:top_n]
        summary = f"{exchange} volatility rank quote={quote} timeframe={timeframe} top_n={top_n}"
        highlights = [f"exchange={exchange}", f"timeframe={timeframe}", f"top_n={top_n}", f"universe={len(symbols)}"]
        meta = {
            "source": "ccxt",
            "exchange_id": client.id,
            "rate_limit_enabled": True,
            "timeout_ms": timeout_ms,
            "cache": {"hit": False, "ttl_s": None},
            "units": {"price": "quote", "volume": "base", "ts": "ms"},
            "precision": {"price_decimals": None, "amount_decimals": None},
            "warnings": [],
        }
        return ok_response(query=q, data={"results": top}, stats={}, summary=summary, highlights=highlights, meta=meta)
    except Exception as e:
        return error_response(
            query=q,
            code="UPSTREAM_ERROR",
            message=str(e),
            context={"method": "fetch_ohlcv", "retryable": True},
        )
```

Create: `/workspace/src/crypto_market_toolkit/scanners/volatility_rank.py` with the code above.

- [ ] **Step 4: Implement `scan_breakouts`**

```python
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from crypto_market_toolkit.exchanges.client import ExchangeClient
from crypto_market_toolkit.indicators.compute import compute_indicators
from crypto_market_toolkit.schemas.response import error_response, ok_response


def _eval_rule(rule: str, *, close: float, indicators: Dict[str, Any]) -> Tuple[bool, str]:
    if rule == "close>bb_upper":
        upper = indicators.get("bbands", {}).get("last", {}).get("upper")
        ok = (upper is not None) and close > upper
        return ok, f"close={close} upper={upper}"
    if rule == "close<bb_lower":
        lower = indicators.get("bbands", {}).get("last", {}).get("lower")
        ok = (lower is not None) and close < lower
        return ok, f"close={close} lower={lower}"
    if rule == "rsi>70":
        rsi = indicators.get("rsi", {}).get("last")
        ok = (rsi is not None) and rsi > 70
        return ok, f"rsi={rsi}"
    if rule == "rsi<30":
        rsi = indicators.get("rsi", {}).get("last")
        ok = (rsi is not None) and rsi < 30
        return ok, f"rsi={rsi}"
    if rule == "macd_cross_up":
        sig = indicators.get("macd", {}).get("signal")
        ok = sig == "macd_cross_up"
        return ok, f"macd_signal={sig}"
    if rule == "macd_cross_down":
        sig = indicators.get("macd", {}).get("signal")
        ok = sig == "macd_cross_down"
        return ok, f"macd_signal={sig}"
    return False, "unsupported_rule"


def scan_breakouts(
    exchange: str,
    *,
    quote: str = "USDT",
    timeframe: str = "1h",
    rule: str = "close>bb_upper",
    top_n: int = 20,
    max_symbols: int = 200,
    market_type: str = "spot",
    indicator_params: Optional[Dict[str, Any]] = None,
    timeout_ms: int = 15000,
) -> Dict[str, Any]:
    q = {
        "exchange": exchange,
        "symbol": None,
        "market_type": market_type,
        "timeframe": timeframe,
        "since_ms": None,
        "limit": top_n,
        "params": {"quote": quote, "rule": rule, "max_symbols": max_symbols},
    }
    try:
        client = ExchangeClient(exchange, market_type=market_type, timeout_ms=timeout_ms)
        markets = client.load_markets_cached()
        symbols = [s for s in markets.keys() if isinstance(s, str) and s.endswith(f"/{quote}")]
        symbols = symbols[:max_symbols]

        results: List[Dict[str, Any]] = []
        for sym in symbols:
            r = compute_indicators(
                exchange,
                sym,
                timeframe=timeframe,
                market_type=market_type,
                indicators=["rsi", "macd", "bbands"],
                indicator_params=indicator_params or {},
                series_tail_size=120,
                timeout_ms=timeout_ms,
            )
            if not r.get("ok"):
                continue
            close = r["stats"].get("close_last")
            if close is None:
                continue
            ok, reason_tail = _eval_rule(rule, close=float(close), indicators=r["data"]["indicators"])
            if not ok:
                continue
            results.append({"symbol": r["query"]["symbol"], "metrics": {"close": close}, "reason": f"rule={rule} {reason_tail}"})

        results = results[:top_n]
        summary = f"{exchange} breakouts rule={rule} timeframe={timeframe} found={len(results)}"
        highlights = [f"exchange={exchange}", f"rule={rule}", f"timeframe={timeframe}", f"found={len(results)}"]
        meta = {
            "source": "ccxt",
            "exchange_id": client.id,
            "rate_limit_enabled": True,
            "timeout_ms": timeout_ms,
            "cache": {"hit": False, "ttl_s": None},
            "units": {"price": "quote", "volume": "base", "ts": "ms"},
            "precision": {"price_decimals": None, "amount_decimals": None},
            "warnings": [],
        }
        return ok_response(query=q, data={"results": results}, stats={}, summary=summary, highlights=highlights, meta=meta)
    except Exception as e:
        return error_response(
            query=q,
            code="UPSTREAM_ERROR",
            message=str(e),
            context={"method": "compute_indicators", "retryable": True},
        )
```

Create: `/workspace/src/crypto_market_toolkit/scanners/breakouts.py` with the code above.

def test_rsi_series_length_matches_input():
    closes = [1, 2, 3, 2, 2, 4, 3, 5, 6, 7, 6, 6, 7, 8, 9, 10]
    out = rsi_series(closes, period=14)
    assert len(out) == len(closes)
    assert out[-1] is not None
```

- [ ] **Step 2: MACD implementation + test**

```python
from crypto_market_toolkit.indicators.macd import macd_series


def test_macd_shapes():
    closes = list(range(1, 200))
    macd, signal, hist = macd_series(closes, fast=12, slow=26, signal=9)
    assert len(macd) == len(signal) == len(hist) == len(closes)
```

- [ ] **Step 3: BBands/ATR/VWAP tests**

```python
from crypto_market_toolkit.indicators.bbands import bbands_series
from crypto_market_toolkit.indicators.atr import atr_series
from crypto_market_toolkit.indicators.vwap import vwap_series


def test_bbands_length():
    closes = list(range(1, 100))
    mid, upper, lower = bbands_series(closes, period=20, stddev=2.0)
    assert len(mid) == len(upper) == len(lower) == len(closes)


def test_atr_length():
    highs = [10, 11, 12, 13, 12, 12, 14]
    lows = [9, 9, 10, 11, 10, 11, 12]
    closes = [9.5, 10, 11, 12, 11.5, 11.8, 13]
    out = atr_series(highs, lows, closes, period=3)
    assert len(out) == len(closes)


def test_vwap_length():
    highs = [10, 11, 12]
    lows = [9, 10, 11]
    closes = [9.5, 10.5, 11.5]
    vols = [100, 200, 150]
    out = vwap_series(highs, lows, closes, vols, window=None)
    assert len(out) == len(closes)
```

- [ ] **Step 4: Run tests**

Run:

```bash
pytest -q
```

Expected: PASS (no network).

---

### Task 9: Document tool usage for AI Agent (README)

**Files:**
- Modify: `/workspace/README.md`

- [ ] **Step 1: Add minimal usage examples**

Include examples:

```python
from crypto_market_toolkit import get_ticker, compute_indicators, scan_top_movers

print(get_ticker("binance", "BTC/USDT")["summary"])
print(compute_indicators("binance", "BTC/USDT", timeframe="1h", indicators=["rsi", "macd"])["highlights"])
print(scan_top_movers("binance")["data"]["results"][:3])
```

---

## Plan self-review checklist

- Covers spec sections: tools list, schema envelope, series tail, cache TTL, retry, symbol normalization, error codes, unit/integration tests.
- No placeholder words; every task has concrete files, code, and commands.
- Field names consistent with design spec (`ok`, `summary`, `highlights`, `query`, `ts_ms`, `iso_time`, `data`, `stats`, `meta`, `error.context.method`, `error.context.retryable`).

## Execution handoff

Plan complete and saved to `/workspace/docs/superpowers/plans/2026-07-03-crypto-market-toolkit.md`. Two execution options:

1. Subagent-Driven (recommended) — I dispatch a fresh subagent per task, review between tasks
2. Inline Execution — execute tasks in this session using executing-plans, with checkpoints

Which approach?
