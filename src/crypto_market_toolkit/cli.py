from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from crypto_market_toolkit import (
    compute_indicators,
    get_ohlcv,
    get_orderbook,
    get_price,
    get_ticker,
    get_trades,
    scan_breakouts,
    scan_top_movers,
    scan_volatility_rank,
    scan_volume_spikes,
)


def _json_arg(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    loaded = json.loads(value)
    if not isinstance(loaded, dict):
        raise argparse.ArgumentTypeError("JSON argument must be an object")
    return loaded


def _csv_arg(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _print_json(data: dict[str, Any], *, pretty: bool) -> None:
    if pretty:
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(json.dumps(data, ensure_ascii=False))


def _base_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = _base_parser("Crypto market toolkit CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    price = subparsers.add_parser("get-price", help="Get last price for a symbol")
    price.add_argument("--exchange", required=True)
    price.add_argument("--symbol", required=True)
    price.add_argument("--market-type", default="spot")
    price.add_argument("--ttl-s", type=float, default=3.0)
    price.add_argument("--timeout-ms", type=int, default=15000)

    ticker = subparsers.add_parser("get-ticker", help="Get ticker snapshot for a symbol")
    ticker.add_argument("--exchange", required=True)
    ticker.add_argument("--symbol", required=True)
    ticker.add_argument("--market-type", default="spot")
    ticker.add_argument("--ttl-s", type=float, default=3.0)
    ticker.add_argument("--timeout-ms", type=int, default=15000)

    ohlcv = subparsers.add_parser("get-ohlcv", help="Get OHLCV candles")
    ohlcv.add_argument("--exchange", required=True)
    ohlcv.add_argument("--symbol", required=True)
    ohlcv.add_argument("--timeframe", default="1m")
    ohlcv.add_argument("--limit", type=int, default=500)
    ohlcv.add_argument("--since-ms", type=int)
    ohlcv.add_argument("--market-type", default="spot")
    ohlcv.add_argument("--full-series", action="store_true")
    ohlcv.add_argument("--series-tail-size", type=int, default=120)
    ohlcv.add_argument("--ttl-s", type=float, default=20.0)
    ohlcv.add_argument("--timeout-ms", type=int, default=15000)

    orderbook = subparsers.add_parser("get-orderbook", help="Get order book snapshot")
    orderbook.add_argument("--exchange", required=True)
    orderbook.add_argument("--symbol", required=True)
    orderbook.add_argument("--limit", type=int, default=100)
    orderbook.add_argument("--market-type", default="spot")
    orderbook.add_argument("--ttl-s", type=float, default=2.0)
    orderbook.add_argument("--timeout-ms", type=int, default=15000)

    trades = subparsers.add_parser("get-trades", help="Get recent trades")
    trades.add_argument("--exchange", required=True)
    trades.add_argument("--symbol", required=True)
    trades.add_argument("--limit", type=int, default=200)
    trades.add_argument("--since-ms", type=int)
    trades.add_argument("--market-type", default="spot")
    trades.add_argument("--ttl-s", type=float, default=3.0)
    trades.add_argument("--timeout-ms", type=int, default=15000)

    indicators = subparsers.add_parser("compute-indicators", help="Compute indicators from OHLCV")
    indicators.add_argument("--exchange", required=True)
    indicators.add_argument("--symbol", required=True)
    indicators.add_argument("--timeframe", default="1h")
    indicators.add_argument("--limit", type=int, default=500)
    indicators.add_argument("--since-ms", type=int)
    indicators.add_argument("--market-type", default="spot")
    indicators.add_argument("--indicators", default="rsi,macd,bbands")
    indicators.add_argument("--indicator-params-json", default="{}")
    indicators.add_argument("--full-series", action="store_true")
    indicators.add_argument("--series-tail-size", type=int, default=120)
    indicators.add_argument("--timeout-ms", type=int, default=15000)

    movers = subparsers.add_parser("scan-top-movers", help="Scan top movers")
    movers.add_argument("--exchange", required=True)
    movers.add_argument("--quote", default="USDT")
    movers.add_argument("--market-type", default="spot")
    movers.add_argument("--top-n", type=int, default=20)
    movers.add_argument("--max-symbols", type=int, default=200)
    movers.add_argument("--timeout-ms", type=int, default=15000)

    spikes = subparsers.add_parser("scan-volume-spikes", help="Scan volume spikes")
    spikes.add_argument("--exchange", required=True)
    spikes.add_argument("--quote", default="USDT")
    spikes.add_argument("--timeframe", default="1h")
    spikes.add_argument("--lookback", type=int, default=48)
    spikes.add_argument("--spike-factor", type=float, default=3.0)
    spikes.add_argument("--top-n", type=int, default=20)
    spikes.add_argument("--max-symbols", type=int, default=200)
    spikes.add_argument("--market-type", default="spot")
    spikes.add_argument("--timeout-ms", type=int, default=15000)

    vol = subparsers.add_parser("scan-volatility-rank", help="Scan symbols by volatility")
    vol.add_argument("--exchange", required=True)
    vol.add_argument("--quote", default="USDT")
    vol.add_argument("--timeframe", default="1h")
    vol.add_argument("--lookback", type=int, default=120)
    vol.add_argument("--top-n", type=int, default=20)
    vol.add_argument("--max-symbols", type=int, default=200)
    vol.add_argument("--market-type", default="spot")
    vol.add_argument("--timeout-ms", type=int, default=15000)

    breakout = subparsers.add_parser("scan-breakouts", help="Scan breakout rules")
    breakout.add_argument("--exchange", required=True)
    breakout.add_argument("--quote", default="USDT")
    breakout.add_argument("--timeframe", default="1h")
    breakout.add_argument("--rule", default="close>bb_upper")
    breakout.add_argument("--top-n", type=int, default=20)
    breakout.add_argument("--max-symbols", type=int, default=200)
    breakout.add_argument("--market-type", default="spot")
    breakout.add_argument("--indicator-params-json", default="{}")
    breakout.add_argument("--timeout-ms", type=int, default=15000)

    return parser


def _dispatch(args: argparse.Namespace) -> dict[str, Any]:
    command = args.command
    if command == "get-price":
        return get_price(
            args.exchange,
            args.symbol,
            market_type=args.market_type,
            ttl_s=args.ttl_s,
            timeout_ms=args.timeout_ms,
        )
    if command == "get-ticker":
        return get_ticker(
            args.exchange,
            args.symbol,
            market_type=args.market_type,
            ttl_s=args.ttl_s,
            timeout_ms=args.timeout_ms,
        )
    if command == "get-ohlcv":
        return get_ohlcv(
            args.exchange,
            args.symbol,
            timeframe=args.timeframe,
            limit=args.limit,
            since_ms=args.since_ms,
            market_type=args.market_type,
            full_series=args.full_series,
            series_tail_size=args.series_tail_size,
            ttl_s=args.ttl_s,
            timeout_ms=args.timeout_ms,
        )
    if command == "get-orderbook":
        return get_orderbook(
            args.exchange,
            args.symbol,
            limit=args.limit,
            market_type=args.market_type,
            ttl_s=args.ttl_s,
            timeout_ms=args.timeout_ms,
        )
    if command == "get-trades":
        return get_trades(
            args.exchange,
            args.symbol,
            limit=args.limit,
            since_ms=args.since_ms,
            market_type=args.market_type,
            ttl_s=args.ttl_s,
            timeout_ms=args.timeout_ms,
        )
    if command == "compute-indicators":
        return compute_indicators(
            args.exchange,
            args.symbol,
            timeframe=args.timeframe,
            limit=args.limit,
            since_ms=args.since_ms,
            market_type=args.market_type,
            indicators=_csv_arg(args.indicators),
            indicator_params=_json_arg(args.indicator_params_json),
            full_series=args.full_series,
            series_tail_size=args.series_tail_size,
            timeout_ms=args.timeout_ms,
        )
    if command == "scan-top-movers":
        return scan_top_movers(
            args.exchange,
            quote=args.quote,
            market_type=args.market_type,
            top_n=args.top_n,
            max_symbols=args.max_symbols,
            timeout_ms=args.timeout_ms,
        )
    if command == "scan-volume-spikes":
        return scan_volume_spikes(
            args.exchange,
            quote=args.quote,
            timeframe=args.timeframe,
            lookback=args.lookback,
            spike_factor=args.spike_factor,
            top_n=args.top_n,
            max_symbols=args.max_symbols,
            market_type=args.market_type,
            timeout_ms=args.timeout_ms,
        )
    if command == "scan-volatility-rank":
        return scan_volatility_rank(
            args.exchange,
            quote=args.quote,
            timeframe=args.timeframe,
            lookback=args.lookback,
            top_n=args.top_n,
            max_symbols=args.max_symbols,
            market_type=args.market_type,
            timeout_ms=args.timeout_ms,
        )
    if command == "scan-breakouts":
        return scan_breakouts(
            args.exchange,
            quote=args.quote,
            timeframe=args.timeframe,
            rule=args.rule,
            top_n=args.top_n,
            max_symbols=args.max_symbols,
            market_type=args.market_type,
            indicator_params=_json_arg(args.indicator_params_json),
            timeout_ms=args.timeout_ms,
        )
    raise ValueError(f"Unsupported command: {command}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        response = _dispatch(args)
    except Exception as exc:  # pragma: no cover - fallback for CLI-level parser/runtime issues
        _print_json(
            {
                "ok": False,
                "summary": str(exc),
                "highlights": [f"cli_error={exc.__class__.__name__}"],
                "query": {"command": getattr(args, "command", None)},
                "ts_ms": None,
                "iso_time": None,
                "data": {},
                "stats": {},
                "meta": {"source": "cli"},
                "error": {
                    "code": "CLI_ERROR",
                    "message": str(exc),
                    "context": {"method": "cli", "retryable": False},
                },
            },
            pretty=getattr(args, "pretty", False),
        )
        return 1

    _print_json(response, pretty=args.pretty)
    return 0 if response.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
