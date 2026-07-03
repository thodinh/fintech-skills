from crypto_market_toolkit.exchanges.client import normalize_symbol


def test_normalize_symbol_passthrough() -> None:
    assert normalize_symbol("BTC/USDT") == ("BTC/USDT", [])


def test_normalize_symbol_compact_pair() -> None:
    symbol, warnings = normalize_symbol("BTCUSDT")
    assert symbol == "BTC/USDT"
    assert warnings
