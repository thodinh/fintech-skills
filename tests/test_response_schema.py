from finance_market_skills.schemas.response import error_response, ok_response


def test_ok_response_has_required_fields() -> None:
    response = ok_response(
        query={"exchange": "binance", "symbol": "BTC/USDT", "market_type": "spot"},
        data={"x": 1},
        stats={"y": 2},
        summary="ok",
        highlights=["x=1"],
        meta={"exchange_id": "binance"},
    )
    assert response["ok"] is True
    assert "summary" in response and isinstance(response["summary"], str)
    assert "highlights" in response and isinstance(response["highlights"], list)
    assert "query" in response and isinstance(response["query"], dict)
    assert "data" in response and isinstance(response["data"], dict)
    assert "stats" in response and isinstance(response["stats"], dict)
    assert "meta" in response and isinstance(response["meta"], dict)
    assert response["error"] is None


def test_error_response_has_required_fields() -> None:
    response = error_response(
        query={"exchange": "binance", "symbol": "BAD", "market_type": "spot"},
        code="INVALID_SYMBOL",
        message="bad symbol",
        context={"method": "fetch_ticker", "retryable": False},
    )
    assert response["ok"] is False
    assert response["error"]["code"] == "INVALID_SYMBOL"
    assert response["error"]["context"]["retryable"] is False
