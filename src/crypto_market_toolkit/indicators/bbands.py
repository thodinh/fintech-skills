from __future__ import annotations

import statistics
from typing import Optional


def bbands_series(
    closes: list[float],
    *,
    period: int = 20,
    stddev: float = 2.0,
) -> tuple[list[Optional[float]], list[Optional[float]], list[Optional[float]]]:
    mid: list[Optional[float]] = [None] * len(closes)
    upper: list[Optional[float]] = [None] * len(closes)
    lower: list[Optional[float]] = [None] * len(closes)
    if period <= 0:
        return mid, upper, lower

    for idx in range(len(closes)):
        if idx < period - 1:
            continue
        window = [float(value) for value in closes[idx - period + 1 : idx + 1]]
        mean = sum(window) / period
        stdev = statistics.pstdev(window) if len(window) >= 2 else 0.0
        mid[idx] = mean
        upper[idx] = mean + stddev * stdev
        lower[idx] = mean - stddev * stdev
    return mid, upper, lower
