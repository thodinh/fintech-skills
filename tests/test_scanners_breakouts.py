from crypto_market_toolkit.scanners.breakouts import _eval_rule, scan_breakouts


class DummyExchangeClient:
    def __init__(self, *args, **kwargs) -> None:
        self.id = "binance"

    def load_markets_cached(self):
        return {"BTC/USDT": {}, "ETH/USDT": {}, "ETH/BTC": {}}


def test_eval_rule_close_above_upper_band() -> None:
    matched, reason = _eval_rule(
        "close>bb_upper",
        close=105.0,
        indicators={"bbands": {"last": {"upper": 100.0}}},
    )
    assert matched is True
    assert "upper=100.0" in reason


def test_scan_breakouts_filters_matching_symbols(monkeypatch) -> None:
    def fake_compute_indicators(exchange, symbol, **kwargs):
        matched = symbol == "BTC/USDT"
        return {
            "ok": True,
            "summary": "ok",
            "highlights": [],
            "query": {"symbol": symbol},
            "ts_ms": 0,
            "iso_time": "1970-01-01T00:00:00+00:00",
            "data": {
                "indicators": {
                    "bbands": {"last": {"upper": 100.0, "lower": 80.0}},
                    "rsi": {"last": 75.0},
                    "macd": {"signal": "macd_cross_up"},
                }
            },
            "stats": {"close_last": 105.0 if matched else 95.0},
            "meta": {},
            "error": None,
        }

    monkeypatch.setattr("crypto_market_toolkit.scanners.breakouts.ExchangeClient", DummyExchangeClient)
    monkeypatch.setattr("crypto_market_toolkit.scanners.breakouts.compute_indicators", fake_compute_indicators)

    response = scan_breakouts("binance", rule="close>bb_upper", top_n=5)

    assert response["ok"] is True
    assert [item["symbol"] for item in response["data"]["results"]] == ["BTC/USDT"]
