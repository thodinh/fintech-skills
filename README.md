# Crypto Market Toolkit

Python toolkit for AI agents to fetch crypto market data from `ccxt`, compute common indicators, and run lightweight market scanners with a JSON-friendly response envelope.

## Features

- Market data tools: `get_price`, `get_ticker`, `get_ohlcv`, `get_orderbook`, `get_trades`
- Indicator tool: `compute_indicators` with `sma`, `ema`, `rsi`, `macd`, `bbands`, `atr`, `vwap`
- Scanner tools: `scan_top_movers`, `scan_volume_spikes`, `scan_volatility_rank`, `scan_breakouts`
- Shared response schema with `summary`, `highlights`, `data`, `stats`, `meta`, and structured errors
- Offline-friendly unit tests for indicator math and orchestration helpers

## Installation

```bash
python -m pip install -e ".[dev]"
```

This also installs the CLI entrypoint:

```bash
crypto-market-toolkit --help
```

## Usage

```python
from crypto_market_toolkit import compute_indicators, get_ticker, scan_top_movers

print(get_ticker("binance", "BTC/USDT")["summary"])
print(
    compute_indicators(
        "binance",
        "BTC/USDT",
        timeframe="1h",
        indicators=["rsi", "macd"],
    )["highlights"]
)
print(scan_top_movers("binance")["data"]["results"][:3])
```

## CLI Usage

```bash
crypto-market-toolkit get-ticker --exchange binance --symbol BTC/USDT --pretty

crypto-market-toolkit compute-indicators \
  --exchange binance \
  --symbol BTC/USDT \
  --timeframe 1h \
  --indicators rsi,macd,bbands \
  --pretty

crypto-market-toolkit scan-top-movers --exchange binance --quote USDT --top-n 10 --pretty
```

## Skill Folder

The repo now includes a ready-to-use root Skill at [SKILL.md](file:///workspace/SKILL.md) with companion metadata at [openai.yaml](file:///workspace/agents/openai.yaml).

Local wrapper:

```bash
/workspace/scripts/run-tool.sh get-price --exchange binance --symbol BTC/USDT --pretty
```

## Response Shape

Successful calls return a dictionary with:

- `ok`: success flag
- `summary`: single-line summary for agents
- `highlights`: list of short facts or signals
- `query`: normalized request payload
- `data`: primary payload
- `stats`: derived metrics
- `meta`: cache/source/warning metadata
- `error`: `None` on success, structured object on failure

## Notes

- Exchange access depends on network availability and exchange uptime.
- Public APIs may differ by market type or symbol support.
- Most scanner functions loop over many symbols, so keep `max_symbols` conservative.
