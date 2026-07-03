from finance_market_skills.indicators.atr import atr_series


def test_atr_length() -> None:
    highs = [10, 11, 12, 13, 12, 12, 14]
    lows = [9, 9, 10, 11, 10, 11, 12]
    closes = [9.5, 10, 11, 12, 11.5, 11.8, 13]
    out = atr_series(highs, lows, closes, period=3)
    assert len(out) == len(closes)
