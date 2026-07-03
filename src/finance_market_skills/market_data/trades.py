from __future__ import annotations

from typing import Any

from finance_market_skills.exchanges.client import ExchangeClient, normalize_symbol
from finance_market_skills.market_data.ticker import _base_query, _market_meta
from finance_market_skills.schemas.response import error_response, ok_response


def get_trades(
    exchange: str,
    symbol: str,
    *,
    limit: int = 200,
    since_ms: int | None = None,
    market_type: str = "spot",
    ttl_s: float = 3.0,
    timeout_ms: int = 15000,
) -> dict[str, Any]:
    query = _base_query(exchange, symbol, market_type, since_ms=since_ms, limit=limit)
    try:
        client = ExchangeClient(exchange, market_type=market_type, timeout_ms=timeout_ms)
        normalized_symbol, warnings = normalize_symbol(symbol)
        client.load_markets_cached()

        raw, cache_meta = client.call_cached(
            cache_key=f"trades:{client.id}:{market_type}:{normalized_symbol}:{since_ms}:{limit}",
            ttl_s=ttl_s,
            method="fetch_trades",
            args=[normalized_symbol, since_ms, limit],
        )

        trades: list[dict[str, Any]] = []
        buy_volume = 0.0
        sell_volume = 0.0
        for trade in raw or []:
            timestamp = trade.get("timestamp")
            price = trade.get("price")
            amount = trade.get("amount")
            side = trade.get("side")
            trades.append({"ts_ms": timestamp, "price": price, "amount": amount, "side": side})
            if isinstance(amount, (int, float)):
                if side == "buy":
                    buy_volume += float(amount)
                elif side == "sell":
                    sell_volume += float(amount)

        ratio = (buy_volume / sell_volume) if sell_volume else None
        data = {"trades": trades, "ts_ms": None}
        stats = {
            "buy_volume": buy_volume,
            "sell_volume": sell_volume,
            "buy_sell_ratio": ratio,
        }
        summary = (
            f"{normalized_symbol} ({exchange} {market_type}) "
            f"trades={len(trades)} buy_sell_ratio={ratio}"
        )
        highlights = [
            f"symbol={normalized_symbol}",
            f"trades_count={len(trades)}",
            f"buy_volume={buy_volume}",
            f"sell_volume={sell_volume}",
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
            context={"method": "fetch_trades", "retryable": True},
        )
