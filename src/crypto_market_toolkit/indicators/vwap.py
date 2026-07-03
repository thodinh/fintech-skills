from __future__ import annotations

from typing import Optional


def vwap_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    volumes: list[float],
    *,
    window: int | None = None,
) -> list[Optional[float]]:
    size = len(closes)
    out: list[Optional[float]] = [None] * size
    if size == 0:
        return out

    cumulative_pv = 0.0
    cumulative_volume = 0.0
    price_volume_history: list[float] = []
    volume_history: list[float] = []

    for idx in range(size):
        typical_price = (float(highs[idx]) + float(lows[idx]) + float(closes[idx])) / 3.0
        volume = float(volumes[idx])
        price_volume = typical_price * volume
        price_volume_history.append(price_volume)
        volume_history.append(volume)
        cumulative_pv += price_volume
        cumulative_volume += volume

        if window is not None and window > 0 and idx >= window:
            cumulative_pv -= price_volume_history[idx - window]
            cumulative_volume -= volume_history[idx - window]

        out[idx] = (cumulative_pv / cumulative_volume) if cumulative_volume else None
    return out
