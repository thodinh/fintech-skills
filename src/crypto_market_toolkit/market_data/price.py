from __future__ import annotations

from typing import Any

from crypto_market_toolkit.market_data.ticker import get_ticker
from crypto_market_toolkit.schemas.response import ok_response


def get_price(
    exchange: str,
    symbol: str,
    *,
    market_type: str = "spot",
    ttl_s: float = 3.0,
    timeout_ms: int = 15000,
) -> dict[str, Any]:
    response = get_ticker(
        exchange,
        symbol,
        market_type=market_type,
        ttl_s=ttl_s,
        timeout_ms=timeout_ms,
    )
    if not response.get("ok"):
        return response

    data = {
        "last": response["data"].get("last"),
        "ts_ms": response["data"].get("ts_ms"),
    }
    stats = {
        "bid": response["data"].get("bid"),
        "ask": response["data"].get("ask"),
        "spread_abs": response["stats"].get("spread_abs"),
        "spread_pct": response["stats"].get("spread_pct"),
    }
    summary = f"{response['query']['symbol']} ({exchange} {market_type}) last={data['last']}"
    highlights = [
        f"symbol={response['query']['symbol']}",
        f"last={data['last']}",
        f"spread_pct={stats.get('spread_pct')}",
    ]
    meta = dict(response.get("meta", {}))
    meta["cache"] = dict(response.get("meta", {}).get("cache", {}))
    return ok_response(
        query=response["query"],
        data=data,
        stats=stats,
        summary=summary,
        highlights=highlights,
        meta=meta,
    )
