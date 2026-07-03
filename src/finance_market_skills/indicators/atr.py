from __future__ import annotations

from typing import Optional


def atr_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 14,
) -> list[Optional[float]]:
    size = len(closes)
    out: list[Optional[float]] = [None] * size
    if period <= 0 or size == 0:
        return out

    true_ranges = [0.0] * size
    for idx in range(size):
        high = float(highs[idx])
        low = float(lows[idx])
        if idx == 0:
            true_ranges[idx] = high - low
        else:
            previous_close = float(closes[idx - 1])
            true_ranges[idx] = max(high - low, abs(high - previous_close), abs(low - previous_close))

    if size < period:
        return out

    atr = sum(true_ranges[:period]) / period
    out[period - 1] = atr
    for idx in range(period, size):
        atr = ((atr * (period - 1)) + true_ranges[idx]) / period
        out[idx] = atr
    return out
