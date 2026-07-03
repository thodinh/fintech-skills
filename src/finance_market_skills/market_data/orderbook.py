from __future__ import annotations

from typing import Any

from finance_market_skills.exchanges.client import ExchangeClient, normalize_symbol
from finance_market_skills.market_data.ticker import _base_query, _market_meta
from finance_market_skills.schemas.response import error_response, ok_response


def _depth_notional(levels: list[list[float]] | list[tuple[float, float]] | None, max_levels: int = 50) -> float:
    total = 0.0
    for price, amount in (levels or [])[:max_levels]:
        if isinstance(price, (int, float)) and isinstance(amount, (int, float)):
            total += float(price) * float(amount)
    return total


def get_orderbook(
    exchange: str,
    symbol: str,
    *,
    limit: int = 100,
    market_type: str = "spot",
    ttl_s: float = 2.0,
    timeout_ms: int = 15000,
) -> dict[str, Any]:
    query = _base_query(exchange, symbol, market_type, limit=limit)
    try:
        client = ExchangeClient(exchange, market_type=market_type, timeout_ms=timeout_ms)
        normalized_symbol, warnings = normalize_symbol(symbol)
        client.load_markets_cached()

        raw, cache_meta = client.call_cached(
            cache_key=f"orderbook:{client.id}:{market_type}:{normalized_symbol}:{limit}",
            ttl_s=ttl_s,
            method="fetch_order_book",
            args=[normalized_symbol, limit],
        )

        bids = raw.get("bids") or []
        asks = raw.get("asks") or []
        best_bid = bids[0][0] if bids else None
        best_ask = asks[0][0] if asks else None
        spread_abs = (
            best_ask - best_bid
            if isinstance(best_ask, (int, float)) and isinstance(best_bid, (int, float))
            else None
        )
        spread_pct = (
            (spread_abs / ((best_ask + best_bid) / 2.0)) * 100.0
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
        summary = (
            f"{normalized_symbol} ({exchange} {market_type}) spread_pct={spread_pct} "
            f"bid={best_bid} ask={best_ask}"
        )
        highlights = [
            f"symbol={normalized_symbol}",
            f"spread_pct={spread_pct}",
            f"best_bid={best_bid}",
            f"best_ask={best_ask}",
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
            context={"method": "fetch_order_book", "retryable": True},
        )
