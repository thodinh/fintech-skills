from __future__ import annotations

from typing import Optional

from finance_market_skills.indicators.moving_averages import ema_series


def macd_series(
    closes: list[float],
    *,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[list[Optional[float]], list[Optional[float]], list[Optional[float]]]:
    ema_fast = ema_series(closes, fast)
    ema_slow = ema_series(closes, slow)

    macd: list[Optional[float]] = [None] * len(closes)
    for idx in range(len(closes)):
        fast_value = ema_fast[idx]
        slow_value = ema_slow[idx]
        macd[idx] = (
            fast_value - slow_value
            if fast_value is not None and slow_value is not None
            else None
        )

    macd_values = [value if value is not None else 0.0 for value in macd]
    signal_line = ema_series(macd_values, signal)

    histogram: list[Optional[float]] = [None] * len(closes)
    for idx in range(len(closes)):
        macd_value = macd[idx]
        signal_value = signal_line[idx]
        histogram[idx] = (
            macd_value - signal_value
            if macd_value is not None and signal_value is not None
            else None
        )
    return macd, signal_line, histogram
