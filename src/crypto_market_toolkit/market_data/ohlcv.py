from __future__ import annotations

import math
import statistics
from typing import Any

from crypto_market_toolkit.exchanges.client import ExchangeClient, normalize_symbol
from crypto_market_toolkit.market_data.ticker import SUPPORTED_MARKET_TYPES, _base_query, _market_meta
from crypto_market_toolkit.schemas.response import error_response, ok_response


def _tail(values: list[Any], size: int) -> list[Any]:
    if size <= 0:
        return []
    return values[-size:] if len(values) > size else values


def _log_returns(closes: list[float]) -> list[float]:
    out: list[float] = []
    for idx in range(1, len(closes)):
        previous = closes[idx - 1]
        current = closes[idx]
        if previous > 0 and current > 0:
            out.append(math.log(current / previous))
    return out


def get_ohlcv(
    exchange: str,
    symbol: str,
    *,
    timeframe: str = "1m",
    limit: int = 500,
    since_ms: int | None = None,
    market_type: str = "spot",
    full_series: bool = False,
    series_tail_size: int = 120,
    ttl_s: float = 20.0,
    timeout_ms: int = 15000,
) -> dict[str, Any]:
    query = _base_query(
        exchange,
        symbol,
        market_type,
        timeframe=timeframe,
        since_ms=since_ms,
        limit=limit,
        params={"full_series": full_series, "series_tail_size": series_tail_size},
    )
    try:
        if market_type not in SUPPORTED_MARKET_TYPES:
            return error_response(
                query=query,
                code="UNSUPPORTED_MARKET_TYPE",
                message=f"Unsupported market_type: {market_type}",
                context={"method": "fetch_ohlcv", "retryable": False},
            )

        client = ExchangeClient(exchange, market_type=market_type, timeout_ms=timeout_ms)
        normalized_symbol, warnings = normalize_symbol(symbol)
        client.load_markets_cached()

        raw, cache_meta = client.call_cached(
            cache_key=(
                f"ohlcv:{client.id}:{market_type}:{normalized_symbol}:"
                f"{timeframe}:{since_ms}:{limit}"
            ),
            ttl_s=ttl_s,
            method="fetch_ohlcv",
            args=[normalized_symbol, timeframe, since_ms, limit],
        )

        ohlcv_full: list[list[Any]] = raw or []
        ohlcv_tail = _tail(ohlcv_full, series_tail_size)
        ohlcv = ohlcv_full if full_series else ohlcv_tail
        closes_tail = [
            float(candle[4])
            for candle in ohlcv_tail
            if candle and len(candle) >= 5 and isinstance(candle[4], (int, float))
        ]

        return_pct = None
        if len(closes_tail) >= 2 and closes_tail[0] != 0:
            return_pct = (closes_tail[-1] / closes_tail[0] - 1.0) * 100.0

        log_returns = _log_returns(closes_tail)
        volatility = statistics.pstdev(log_returns) if len(log_returns) >= 2 else None

        ranges_pct: list[float] = []
        volumes: list[float] = []
        for candle in ohlcv_tail:
            if not candle or len(candle) < 6:
                continue
            high = candle[2]
            low = candle[3]
            close = candle[4]
            volume = candle[5]
            if (
                isinstance(high, (int, float))
                and isinstance(low, (int, float))
                and isinstance(close, (int, float))
                and close
            ):
                ranges_pct.append(((high - low) / close) * 100.0)
            if isinstance(volume, (int, float)):
                volumes.append(float(volume))

        stats = {
            "return_pct": return_pct,
            "volatility": volatility,
            "avg_range_pct": (sum(ranges_pct) / len(ranges_pct)) if ranges_pct else None,
            "avg_volume": (sum(volumes) / len(volumes)) if volumes else None,
        }
        data = {
            "ohlcv": ohlcv,
            "ohlcv_tail": ohlcv_tail,
            "last_candle": ohlcv_tail[-1] if ohlcv_tail else None,
            "series_full_truncated": (not full_series) and (len(ohlcv_full) > len(ohlcv_tail)),
            "series_tail_size": series_tail_size,
        }
        last_close = closes_tail[-1] if closes_tail else None
        summary = (
            f"{normalized_symbol} ({exchange} {market_type}) ohlcv {timeframe} "
            f"last_close={last_close} return_pct={return_pct}"
        )
        highlights = [
            f"symbol={normalized_symbol}",
            f"timeframe={timeframe}",
            f"last_close={last_close}",
            f"return_pct={return_pct}",
            f"volatility={volatility}",
        ]
        meta = _market_meta(
            client=client,
            timeout_ms=timeout_ms,
            cache_meta=cache_meta,
            warnings=warnings,
        )
        query["symbol"] = normalized_symbol
        return ok_response(
            query=query,
            data=data,
            stats=stats,
            summary=summary,
            highlights=highlights,
            meta=meta,
        )
    except Exception as exc:
        return error_response(
            query=query,
            code="UPSTREAM_ERROR",
            message=str(exc),
            context={"method": "fetch_ohlcv", "retryable": True},
        )
