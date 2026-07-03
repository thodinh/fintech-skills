from __future__ import annotations

from typing import Any

from crypto_market_toolkit.exchanges.client import ExchangeClient
from crypto_market_toolkit.schemas.response import error_response, ok_response


def _scanner_meta(client: ExchangeClient, timeout_ms: int) -> dict[str, Any]:
    return {
        "source": "ccxt",
        "exchange_id": client.id,
        "rate_limit_enabled": True,
        "timeout_ms": timeout_ms,
        "cache": {"hit": False, "ttl_s": None},
        "units": {"price": "quote", "volume": "base", "ts": "ms"},
        "precision": {"price_decimals": None, "amount_decimals": None},
        "warnings": [],
    }


def scan_top_movers(
    exchange: str,
    *,
    quote: str = "USDT",
    market_type: str = "spot",
    top_n: int = 20,
    max_symbols: int = 200,
    timeout_ms: int = 15000,
) -> dict[str, Any]:
    query = {
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
        symbols = [symbol for symbol in markets if isinstance(symbol, str) and symbol.endswith(f"/{quote}")]
        symbols = symbols[:max_symbols]

        results: list[dict[str, Any]] = []
        for symbol in symbols:
            raw, _ = client.call_cached(
                cache_key=f"ticker:{client.id}:{market_type}:{symbol}",
                ttl_s=3.0,
                method="fetch_ticker",
                args=[symbol],
            )
            pct_24h = raw.get("percentage")
            quote_volume = raw.get("quoteVolume")
            results.append(
                {
                    "symbol": symbol,
                    "metrics": {
                        "pct_24h": pct_24h,
                        "quote_volume": quote_volume,
                        "last": raw.get("last"),
                    },
                    "reason": f"pct_24h={pct_24h} quote_volume={quote_volume}",
                }
            )

        results.sort(
            key=lambda item: (
                item["metrics"]["pct_24h"] is not None,
                item["metrics"]["pct_24h"],
            ),
            reverse=True,
        )
        top = results[:top_n]
        summary = f"{exchange} movers quote={quote} top_n={top_n} universe={len(symbols)}"
        highlights = [
            f"exchange={exchange}",
            f"quote={quote}",
            f"top_n={top_n}",
            f"universe={len(symbols)}",
        ]
        return ok_response(
            query=query,
            data={"results": top},
            stats={},
            summary=summary,
            highlights=highlights,
            meta=_scanner_meta(client, timeout_ms),
        )
    except Exception as exc:
        return error_response(
            query=query,
            code="UPSTREAM_ERROR",
            message=str(exc),
            context={"method": "fetch_ticker", "retryable": True},
        )
