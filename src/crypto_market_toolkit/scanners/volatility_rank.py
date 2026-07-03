from __future__ import annotations

import math
import statistics
from typing import Any

from crypto_market_toolkit.exchanges.client import ExchangeClient
from crypto_market_toolkit.market_data.ohlcv import get_ohlcv
from crypto_market_toolkit.schemas.response import error_response, ok_response
from crypto_market_toolkit.scanners.top_movers import _scanner_meta


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
) -> dict[str, Any]:
    query = {
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
        symbols = [symbol for symbol in markets if isinstance(symbol, str) and symbol.endswith(f"/{quote}")]
        symbols = symbols[:max_symbols]

        results: list[dict[str, Any]] = []
        for symbol in symbols:
            response = get_ohlcv(
                exchange,
                symbol,
                timeframe=timeframe,
                limit=max(lookback, 20),
                market_type=market_type,
                series_tail_size=max(lookback, 20),
                timeout_ms=timeout_ms,
            )
            if not response.get("ok"):
                continue
            tail = response["data"].get("ohlcv_tail") or []
            closes = [float(candle[4]) for candle in tail if candle and len(candle) >= 5]
            if len(closes) < 3:
                continue
            log_returns = []
            for idx in range(1, len(closes)):
                previous = closes[idx - 1]
                current = closes[idx]
                if previous > 0 and current > 0:
                    log_returns.append(math.log(current / previous))
            volatility = statistics.pstdev(log_returns) if len(log_returns) >= 2 else 0.0
            results.append(
                {
                    "symbol": symbol,
                    "metrics": {"volatility": volatility},
                    "reason": f"volatility={volatility}",
                }
            )

        results.sort(key=lambda item: item["metrics"]["volatility"], reverse=True)
        top = results[:top_n]
        summary = f"{exchange} volatility rank quote={quote} timeframe={timeframe} top_n={top_n}"
        highlights = [
            f"exchange={exchange}",
            f"timeframe={timeframe}",
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
            context={"method": "fetch_ohlcv", "retryable": True},
        )
