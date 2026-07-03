from __future__ import annotations

from typing import Any

from crypto_market_toolkit.exchanges.client import ExchangeClient
from crypto_market_toolkit.market_data.ohlcv import get_ohlcv
from crypto_market_toolkit.schemas.response import error_response, ok_response
from crypto_market_toolkit.scanners.top_movers import _scanner_meta


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
) -> dict[str, Any]:
    query = {
        "exchange": exchange,
        "symbol": None,
        "market_type": market_type,
        "timeframe": timeframe,
        "since_ms": None,
        "limit": top_n,
        "params": {
            "quote": quote,
            "lookback": lookback,
            "spike_factor": spike_factor,
            "max_symbols": max_symbols,
        },
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
                limit=max(lookback, 10),
                market_type=market_type,
                series_tail_size=max(lookback, 10),
                timeout_ms=timeout_ms,
            )
            if not response.get("ok"):
                continue
            tail = response["data"].get("ohlcv_tail") or []
            volumes = [float(candle[5]) for candle in tail if candle and len(candle) >= 6]
            if len(volumes) < 2:
                continue
            last_volume = volumes[-1]
            baseline = volumes[-lookback:] if len(volumes) >= lookback else volumes
            average_volume = (sum(baseline) / len(baseline)) if baseline else 0.0
            spike = (last_volume / average_volume) if average_volume else None
            if spike is None or spike < spike_factor:
                continue
            results.append(
                {
                    "symbol": symbol,
                    "metrics": {
                        "spike": spike,
                        "volume_last": last_volume,
                        "avg_volume": average_volume,
                    },
                    "reason": f"volume_spike={spike}x last={last_volume} avg={average_volume}",
                }
            )

        results.sort(key=lambda item: item["metrics"]["spike"], reverse=True)
        top = results[:top_n]
        summary = f"{exchange} volume spikes quote={quote} timeframe={timeframe} found={len(top)}"
        highlights = [
            f"exchange={exchange}",
            f"timeframe={timeframe}",
            f"found={len(top)}",
            f"spike_factor={spike_factor}",
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
