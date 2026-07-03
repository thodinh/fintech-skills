"""Crypto market toolkit package."""

__all__ = [
    "get_price",
    "get_ticker",
    "get_ohlcv",
    "get_orderbook",
    "get_trades",
    "compute_indicators",
    "scan_top_movers",
    "scan_volume_spikes",
    "scan_volatility_rank",
    "scan_breakouts",
]


def _pending_tool(name: str):
    def _placeholder(*args, **kwargs):
        raise NotImplementedError(
            f"{name} is not implemented yet. Complete later crypto-market-toolkit tasks first."
        )

    _placeholder.__name__ = name
    return _placeholder


get_price = _pending_tool("get_price")
get_ticker = _pending_tool("get_ticker")
get_ohlcv = _pending_tool("get_ohlcv")
get_orderbook = _pending_tool("get_orderbook")
get_trades = _pending_tool("get_trades")
compute_indicators = _pending_tool("compute_indicators")
scan_top_movers = _pending_tool("scan_top_movers")
scan_volume_spikes = _pending_tool("scan_volume_spikes")
scan_volatility_rank = _pending_tool("scan_volatility_rank")
scan_breakouts = _pending_tool("scan_breakouts")
