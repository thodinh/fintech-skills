from __future__ import annotations

from typing import Any

from crypto_market_toolkit.exchanges.client import ExchangeClient
from crypto_market_toolkit.indicators.compute import compute_indicators
from crypto_market_toolkit.schemas.response import error_response, ok_response
from crypto_market_toolkit.scanners.top_movers import _scanner_meta


def _eval_rule(rule: str, *, close: float, indicators: dict[str, Any]) -> tuple[bool, str]:
    if rule == "close>bb_upper":
        upper = indicators.get("bbands", {}).get("last", {}).get("upper")
        matched = (upper is not None) and close > upper
        return matched, f"close={close} upper={upper}"
    if rule == "close<bb_lower":
        lower = indicators.get("bbands", {}).get("last", {}).get("lower")
        matched = (lower is not None) and close < lower
        return matched, f"close={close} lower={lower}"
    if rule == "rsi>70":
        rsi = indicators.get("rsi", {}).get("last")
        matched = (rsi is not None) and rsi > 70
        return matched, f"rsi={rsi}"
    if rule == "rsi<30":
        rsi = indicators.get("rsi", {}).get("last")
        matched = (rsi is not None) and rsi < 30
        return matched, f"rsi={rsi}"
    if rule == "macd_cross_up":
        signal = indicators.get("macd", {}).get("signal")
        matched = signal == "macd_cross_up"
        return matched, f"macd_signal={signal}"
    if rule == "macd_cross_down":
        signal = indicators.get("macd", {}).get("signal")
        matched = signal == "macd_cross_down"
        return matched, f"macd_signal={signal}"
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
    indicator_params: dict[str, Any] | None = None,
    timeout_ms: int = 15000,
) -> dict[str, Any]:
    query = {
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
        symbols = [symbol for symbol in markets if isinstance(symbol, str) and symbol.endswith(f"/{quote}")]
        symbols = symbols[:max_symbols]

        results: list[dict[str, Any]] = []
        for symbol in symbols:
            response = compute_indicators(
                exchange,
                symbol,
                timeframe=timeframe,
                market_type=market_type,
                indicators=["rsi", "macd", "bbands"],
                indicator_params=indicator_params or {},
                series_tail_size=120,
                timeout_ms=timeout_ms,
            )
            if not response.get("ok"):
                continue
            close = response["stats"].get("close_last")
            if close is None:
                continue
            matched, detail = _eval_rule(rule, close=float(close), indicators=response["data"]["indicators"])
            if not matched:
                continue
            results.append(
                {
                    "symbol": response["query"]["symbol"],
                    "metrics": {"close": close},
                    "reason": f"rule={rule} {detail}",
                }
            )

        results = results[:top_n]
        summary = f"{exchange} breakouts rule={rule} timeframe={timeframe} found={len(results)}"
        highlights = [
            f"exchange={exchange}",
            f"rule={rule}",
            f"timeframe={timeframe}",
            f"found={len(results)}",
        ]
        return ok_response(
            query=query,
            data={"results": results},
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
            context={"method": "compute_indicators", "retryable": True},
        )
