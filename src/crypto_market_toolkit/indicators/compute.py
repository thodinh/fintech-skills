from __future__ import annotations

from typing import Any

from crypto_market_toolkit.indicators.atr import atr_series
from crypto_market_toolkit.indicators.bbands import bbands_series
from crypto_market_toolkit.indicators.macd import macd_series
from crypto_market_toolkit.indicators.moving_averages import ema_series, sma_series
from crypto_market_toolkit.indicators.rsi import rsi_series
from crypto_market_toolkit.indicators.vwap import vwap_series
from crypto_market_toolkit.market_data.ohlcv import get_ohlcv
from crypto_market_toolkit.schemas.response import error_response, ok_response


def _signal_rsi(last: float | None) -> str | None:
    if last is None:
        return None
    if last < 30:
        return "rsi_state=oversold"
    if last > 70:
        return "rsi_state=overbought"
    return "rsi_state=neutral"


def _signal_macd(histogram: list[float | None]) -> str | None:
    if len(histogram) < 2:
        return None
    previous = histogram[-2]
    current = histogram[-1]
    if previous is None or current is None:
        return None
    if previous <= 0 and current > 0:
        return "macd_cross_up"
    if previous >= 0 and current < 0:
        return "macd_cross_down"
    return None


def _signal_bbands(close: float | None, upper: float | None, lower: float | None) -> str | None:
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
    since_ms: int | None = None,
    market_type: str = "spot",
    indicators: list[str] | None = None,
    indicator_params: dict[str, Any] | None = None,
    full_series: bool = False,
    series_tail_size: int = 120,
    timeout_ms: int = 15000,
) -> dict[str, Any]:
    indicators = indicators or ["rsi", "macd", "bbands"]
    indicator_params = indicator_params or {}
    query = {
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

    ohlcv_response = get_ohlcv(
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
    if not ohlcv_response.get("ok"):
        return ohlcv_response

    ohlcv_tail = ohlcv_response["data"].get("ohlcv_tail") or []
    if not ohlcv_tail:
        return error_response(
            query=query,
            code="UPSTREAM_ERROR",
            message="No OHLCV returned",
            context={"method": "fetch_ohlcv", "retryable": True},
        )

    highs = [float(candle[2]) for candle in ohlcv_tail]
    lows = [float(candle[3]) for candle in ohlcv_tail]
    closes = [float(candle[4]) for candle in ohlcv_tail]
    volumes = [float(candle[5]) for candle in ohlcv_tail]

    computed: dict[str, Any] = {}
    signals: list[str] = []

    for name in indicators:
        if name.startswith("sma"):
            period = int(indicator_params.get(name, {}).get("period", 20))
            series = sma_series(closes, period)
            computed[name] = {"params": {"period": period}, "series_tail": series, "last": series[-1], "signal": None}
        elif name.startswith("ema"):
            period = int(indicator_params.get(name, {}).get("period", 20))
            series = ema_series(closes, period)
            computed[name] = {"params": {"period": period}, "series_tail": series, "last": series[-1], "signal": None}
        elif name == "rsi":
            period = int(indicator_params.get("rsi", {}).get("period", 14))
            series = rsi_series(closes, period=period)
            signal = _signal_rsi(series[-1])
            computed["rsi"] = {"params": {"period": period}, "series_tail": series, "last": series[-1], "signal": signal}
            if signal:
                signals.append(signal)
        elif name == "macd":
            params = indicator_params.get("macd", {})
            fast = int(params.get("fast", 12))
            slow = int(params.get("slow", 26))
            signal_period = int(params.get("signal", 9))
            macd_line, signal_line, histogram = macd_series(
                closes,
                fast=fast,
                slow=slow,
                signal=signal_period,
            )
            signal = _signal_macd(histogram)
            computed["macd"] = {
                "params": {"fast": fast, "slow": slow, "signal": signal_period},
                "series_tail": {"macd": macd_line, "signal": signal_line, "hist": histogram},
                "last": {"macd": macd_line[-1], "signal": signal_line[-1], "hist": histogram[-1]},
                "signal": signal,
            }
            if signal:
                signals.append(signal)
        elif name == "bbands":
            params = indicator_params.get("bbands", {})
            period = int(params.get("period", 20))
            stddev = float(params.get("stddev", 2.0))
            mid, upper, lower = bbands_series(closes, period=period, stddev=stddev)
            signal = _signal_bbands(closes[-1], upper[-1], lower[-1])
            computed["bbands"] = {
                "params": {"period": period, "stddev": stddev},
                "series_tail": {"mid": mid, "upper": upper, "lower": lower},
                "last": {"mid": mid[-1], "upper": upper[-1], "lower": lower[-1]},
                "signal": signal,
            }
            if signal:
                signals.append(signal)
        elif name == "atr":
            period = int(indicator_params.get("atr", {}).get("period", 14))
            series = atr_series(highs, lows, closes, period=period)
            computed["atr"] = {"params": {"period": period}, "series_tail": series, "last": series[-1], "signal": None}
        elif name == "vwap":
            params = indicator_params.get("vwap", {})
            window = params.get("window")
            normalized_window = int(window) if window is not None else None
            series = vwap_series(highs, lows, closes, volumes, window=normalized_window)
            computed["vwap"] = {
                "params": {"window": normalized_window},
                "series_tail": series,
                "last": series[-1],
                "signal": None,
            }

    last_close = closes[-1] if closes else None
    summary = (
        f"{ohlcv_response['query']['symbol']} ({exchange} {market_type}) {timeframe} "
        f"close={last_close} signals={','.join(signals) if signals else 'none'}"
    )
    highlights = [
        f"symbol={ohlcv_response['query']['symbol']}",
        f"timeframe={timeframe}",
        f"close_last={last_close}",
        *signals[:3],
    ]
    data = {"ohlcv_tail": ohlcv_tail, "indicators": computed}
    stats = {
        "close_last": last_close,
        "return_pct_tail": ohlcv_response["stats"].get("return_pct"),
        "volatility": ohlcv_response["stats"].get("volatility"),
    }
    return ok_response(
        query=ohlcv_response["query"],
        data=data,
        stats=stats,
        summary=summary,
        highlights=highlights,
        meta=ohlcv_response.get("meta", {}),
    )
