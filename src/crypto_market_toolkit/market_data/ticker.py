from __future__ import annotations

from typing import Any

from crypto_market_toolkit.exchanges.client import ExchangeClient, normalize_symbol
from crypto_market_toolkit.schemas.response import error_response, ok_response

SUPPORTED_MARKET_TYPES = {"spot", "swap", "future"}


def _base_query(
    exchange: str,
    symbol: str,
    market_type: str,
    *,
    timeframe: str | None = None,
    since_ms: int | None = None,
    limit: int | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "exchange": exchange,
        "symbol": symbol,
        "market_type": market_type,
        "timeframe": timeframe,
        "since_ms": since_ms,
        "limit": limit,
        "params": params or {},
    }


def _market_meta(
    *,
    client: ExchangeClient,
    timeout_ms: int,
    cache_meta: dict[str, Any],
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "source": "ccxt",
        "exchange_id": client.id,
        "rate_limit_enabled": True,
        "timeout_ms": timeout_ms,
        "cache": cache_meta["cache"],
        "units": {"price": "quote", "volume": "base", "ts": "ms"},
        "precision": {"price_decimals": None, "amount_decimals": None},
        "warnings": warnings,
    }


def get_ticker(
    exchange: str,
    symbol: str,
    *,
    market_type: str = "spot",
    ttl_s: float = 3.0,
    timeout_ms: int = 15000,
) -> dict[str, Any]:
    query = _base_query(exchange, symbol, market_type)
    try:
        if market_type not in SUPPORTED_MARKET_TYPES:
            return error_response(
                query=query,
                code="UNSUPPORTED_MARKET_TYPE",
                message=f"Unsupported market_type: {market_type}",
                context={"method": "fetch_ticker", "retryable": False},
            )

        client = ExchangeClient(exchange, market_type=market_type, timeout_ms=timeout_ms)
        normalized_symbol, warnings = normalize_symbol(symbol)
        client.load_markets_cached()

        raw, cache_meta = client.call_cached(
            cache_key=f"ticker:{client.id}:{market_type}:{normalized_symbol}",
            ttl_s=ttl_s,
            method="fetch_ticker",
            args=[normalized_symbol],
        )

        last = raw.get("last")
        bid = raw.get("bid")
        ask = raw.get("ask")
        spread_abs = (
            ask - bid if isinstance(ask, (int, float)) and isinstance(bid, (int, float)) else None
        )
        spread_pct = (
            (spread_abs / ((ask + bid) / 2.0)) * 100.0
            if spread_abs is not None and (ask + bid) != 0
            else None
        )

        high = raw.get("high")
        low = raw.get("low")
        range_pct = (
            ((high - low) / ((bid + ask) / 2.0)) * 100.0
            if all(isinstance(x, (int, float)) for x in [high, low, bid, ask]) and (bid + ask) != 0
            else None
        )

        data = {
            "last": last,
            "bid": bid,
            "ask": ask,
            "open": raw.get("open"),
            "high": high,
            "low": low,
            "base_volume": raw.get("baseVolume"),
            "quote_volume": raw.get("quoteVolume"),
            "change": raw.get("change"),
            "percentage": raw.get("percentage"),
            "ts_ms": raw.get("timestamp"),
        }
        stats = {
            "spread_abs": spread_abs,
            "spread_pct": spread_pct,
            "range_pct": range_pct,
        }
        summary = (
            f"{normalized_symbol} ({exchange} {market_type}) "
            f"last={last} pct_24h={data.get('percentage')}"
        )
        highlights = [
            f"symbol={normalized_symbol}",
            f"last={last}",
            f"pct_24h={data.get('percentage')}",
            f"spread_pct={spread_pct}",
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
            context={"method": "fetch_ticker", "retryable": True},
        )
