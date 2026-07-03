from finance_market_skills.indicators.macd import macd_series


def test_macd_shapes() -> None:
    closes = list(range(1, 200))
    macd, signal, hist = macd_series(closes, fast=12, slow=26, signal=9)
    assert len(macd) == len(signal) == len(hist) == len(closes)
