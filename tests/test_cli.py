import json

from finance_market_skills.cli import main


def test_cli_get_ticker_prints_json(monkeypatch, capsys) -> None:
    def fake_get_ticker(exchange, symbol, **kwargs):
        return {
            "ok": True,
            "summary": "BTC/USDT ok",
            "highlights": ["symbol=BTC/USDT"],
            "query": {"exchange": exchange, "symbol": symbol},
            "ts_ms": 0,
            "iso_time": "1970-01-01T00:00:00+00:00",
            "data": {"last": 100.0},
            "stats": {},
            "meta": {"source": "test"},
            "error": None,
        }

    monkeypatch.setattr("finance_market_skills.cli.get_ticker", fake_get_ticker)

    exit_code = main(["get-ticker", "--exchange", "binance", "--symbol", "BTC/USDT"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["data"]["last"] == 100.0


def test_cli_compute_indicators_parses_json_args(monkeypatch, capsys) -> None:
    def fake_compute_indicators(exchange, symbol, **kwargs):
        return {
            "ok": True,
            "summary": "indicators ok",
            "highlights": [f"indicators={kwargs['indicators']}"],
            "query": {"exchange": exchange, "symbol": symbol},
            "ts_ms": 0,
            "iso_time": "1970-01-01T00:00:00+00:00",
            "data": {"params": kwargs["indicator_params"]},
            "stats": {},
            "meta": {"source": "test"},
            "error": None,
        }

    monkeypatch.setattr("finance_market_skills.cli.compute_indicators", fake_compute_indicators)

    exit_code = main(
        [
            "compute-indicators",
            "--exchange",
            "binance",
            "--symbol",
            "BTC/USDT",
            "--indicators",
            "rsi,macd",
            "--indicator-params-json",
            '{"rsi":{"period":14}}',
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["data"]["params"]["rsi"]["period"] == 14
