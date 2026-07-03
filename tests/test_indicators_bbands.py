from crypto_market_toolkit.indicators.bbands import bbands_series


def test_bbands_length() -> None:
    closes = list(range(1, 100))
    mid, upper, lower = bbands_series(closes, period=20, stddev=2.0)
    assert len(mid) == len(upper) == len(lower) == len(closes)
