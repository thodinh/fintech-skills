from finance_market_skills.indicators.rsi import rsi_series


def test_rsi_series_length_matches_input() -> None:
    closes = [1, 2, 3, 2, 2, 4, 3, 5, 6, 7, 6, 6, 7, 8, 9, 10]
    out = rsi_series(closes, period=14)
    assert len(out) == len(closes)
    assert out[-1] is not None
