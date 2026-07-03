from crypto_market_toolkit.indicators.compute import compute_indicators


def test_compute_indicators_with_mocked_ohlcv(monkeypatch) -> None:
    candles = [
        [idx * 60_000, 100 + idx, 101 + idx, 99 + idx, 100 + idx, 1_000 + idx * 10]
        for idx in range(1, 80)
    ]

    def fake_get_ohlcv(*args, **kwargs):
        return {
            "ok": True,
            "summary": "ok",
            "highlights": [],
            "query": {"exchange": "binance", "symbol": "BTC/USDT", "market_type": "spot", "timeframe": "1h", "since_ms": None, "limit": 79, "params": {}},
            "ts_ms": 0,
            "iso_time": "1970-01-01T00:00:00+00:00",
            "data": {"ohlcv_tail": candles},
            "stats": {"return_pct": 1.0, "volatility": 0.2},
            "meta": {"source": "ccxt"},
            "error": None,
        }

    monkeypatch.setattr("crypto_market_toolkit.indicators.compute.get_ohlcv", fake_get_ohlcv)

    response = compute_indicators(
        "binance",
        "BTC/USDT",
        indicators=["rsi", "macd", "bbands", "atr", "vwap", "sma_20", "ema_20"],
        indicator_params={"sma_20": {"period": 20}, "ema_20": {"period": 20}},
    )

    assert response["ok"] is True
    assert response["data"]["indicators"]["rsi"]["last"] is not None
    assert response["data"]["indicators"]["macd"]["last"]["hist"] is not None
    assert response["stats"]["close_last"] == candles[-1][4]
