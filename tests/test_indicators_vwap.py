from finance_market_skills.indicators.vwap import vwap_series


def test_vwap_length() -> None:
    highs = [10, 11, 12]
    lows = [9, 10, 11]
    closes = [9.5, 10.5, 11.5]
    volumes = [100, 200, 150]
    out = vwap_series(highs, lows, closes, volumes, window=None)
    assert len(out) == len(closes)
