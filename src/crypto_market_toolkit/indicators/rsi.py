from __future__ import annotations

from typing import Optional


def rsi_series(closes: list[float], period: int = 14) -> list[Optional[float]]:
    out: list[Optional[float]] = [None] * len(closes)
    if period <= 0 or len(closes) <= period:
        return out

    gains = [0.0] * len(closes)
    losses = [0.0] * len(closes)
    for idx in range(1, len(closes)):
        delta = float(closes[idx]) - float(closes[idx - 1])
        gains[idx] = delta if delta > 0 else 0.0
        losses[idx] = -delta if delta < 0 else 0.0

    avg_gain = sum(gains[1 : period + 1]) / period
    avg_loss = sum(losses[1 : period + 1]) / period
    out[period] = 100.0 if avg_loss == 0 else 100.0 - (100.0 / (1.0 + (avg_gain / avg_loss)))

    for idx in range(period + 1, len(closes)):
        avg_gain = ((avg_gain * (period - 1)) + gains[idx]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[idx]) / period
        out[idx] = 100.0 if avg_loss == 0 else 100.0 - (100.0 / (1.0 + (avg_gain / avg_loss)))
    return out
