from __future__ import annotations

from typing import Optional


def sma_series(values: list[float], period: int) -> list[Optional[float]]:
    out: list[Optional[float]] = [None] * len(values)
    if period <= 0:
        return out

    window_sum = 0.0
    for idx, value in enumerate(values):
        window_sum += float(value)
        if idx >= period:
            window_sum -= float(values[idx - period])
        if idx >= period - 1:
            out[idx] = window_sum / period
    return out


def ema_series(values: list[float], period: int) -> list[Optional[float]]:
    out: list[Optional[float]] = [None] * len(values)
    if period <= 0 or not values:
        return out

    factor = 2.0 / (period + 1.0)
    ema: float | None = None
    for idx, value in enumerate(values):
        current = float(value)
        if ema is None:
            ema = current
        else:
            ema = (current - ema) * factor + ema
        out[idx] = ema
    return out
