from __future__ import annotations

from typing import Any

SUPPORTED_EXCHANGES: dict[str, str] = {
    "binance": "binance",
    "bybit": "bybit",
    "okx": "okx",
}


def create_exchange(exchange: str, *, market_type: str = "spot", timeout_ms: int = 15000) -> Any:
    ex_id = SUPPORTED_EXCHANGES.get(exchange.lower())
    if not ex_id:
        raise ValueError(f"Unsupported exchange: {exchange}")

    import ccxt

    cls = getattr(ccxt, ex_id)
    options: dict[str, Any] = {}
    if market_type in {"spot", "swap", "future"}:
        options["defaultType"] = market_type

    return cls(
        {
            "enableRateLimit": True,
            "timeout": timeout_ms,
            "options": options,
        }
    )
