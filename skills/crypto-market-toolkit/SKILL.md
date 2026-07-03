---
name: crypto-market-toolkit
description: "Use when the user asks for crypto token prices, ticker data, OHLCV candles, order books, trades, technical indicators, or market scans powered by ccxt."
allowed-tools: Bash(crypto-market-toolkit:*), Bash(python -m crypto_market_toolkit.cli:*), Bash(./skills/crypto-market-toolkit/scripts/run-tool.sh:*)
---

# Crypto Market Toolkit

Use this Skill when you need a strong finance toolset for crypto market data. It wraps the local `crypto_market_toolkit` package and returns structured JSON that is friendly for AI agents:

- `ok`, `summary`, `highlights`
- `query`, `data`, `stats`, `meta`
- structured `error`

This Skill is market-data only. It does **not** place orders or use API keys.

## When To Use

Use this Skill when the user asks for:

- token prices or ticker snapshots
- OHLCV / candle history
- order book depth or recent trades
- indicators such as RSI, MACD, EMA, SMA, Bollinger Bands, ATR, VWAP
- market scans such as top movers, volume spikes, volatility rank, breakout rules

Do not use this Skill for:

- on-chain data
- DEX routing or swaps
- live account trading

## Install

From the project root:

```bash
python -m pip install -e ".[dev]"
```

You can then call either:

```bash
crypto-market-toolkit --help
```

or:

```bash
python -m crypto_market_toolkit.cli --help
```

or the repo-local wrapper:

```bash
./skills/crypto-market-toolkit/scripts/run-tool.sh --help
```

## Core Commands

### Price / Ticker

```bash
crypto-market-toolkit get-price --exchange binance --symbol BTC/USDT --pretty
crypto-market-toolkit get-ticker --exchange bybit --symbol ETH/USDT --market-type spot --pretty
```

### OHLCV / Order Book / Trades

```bash
crypto-market-toolkit get-ohlcv --exchange binance --symbol BTC/USDT --timeframe 1h --limit 200 --series-tail-size 120 --pretty
crypto-market-toolkit get-orderbook --exchange okx --symbol SOL/USDT --limit 50 --pretty
crypto-market-toolkit get-trades --exchange bybit --symbol BTC/USDT --limit 100 --pretty
```

### Indicators

```bash
crypto-market-toolkit compute-indicators \
  --exchange binance \
  --symbol BTC/USDT \
  --timeframe 1h \
  --indicators rsi,macd,bbands,ema_20 \
  --indicator-params-json '{"ema_20":{"period":20},"bbands":{"period":20,"stddev":2.0}}' \
  --pretty
```

### Scanners

```bash
crypto-market-toolkit scan-top-movers --exchange binance --quote USDT --top-n 10 --pretty
crypto-market-toolkit scan-volume-spikes --exchange binance --quote USDT --timeframe 1h --lookback 48 --spike-factor 3 --pretty
crypto-market-toolkit scan-volatility-rank --exchange okx --quote USDT --timeframe 4h --top-n 10 --pretty
crypto-market-toolkit scan-breakouts --exchange bybit --quote USDT --timeframe 1h --rule close>bb_upper --pretty
```

## Recommended Agent Workflow

1. Pick the smallest command that answers the question.
2. Prefer `get-price` or `get-ticker` for simple price questions.
3. Use `compute-indicators` when the user asks for technical analysis.
4. Use scanner commands when the user asks for discovery across many symbols.
5. Read `summary` and `highlights` first, then inspect `data` and `stats` only if needed.

## Output Contract

Every command returns JSON. Typical success shape:

```json
{
  "ok": true,
  "summary": "BTC/USDT (binance spot) last=65000 pct_24h=2.1",
  "highlights": ["symbol=BTC/USDT", "last=65000", "pct_24h=2.1"],
  "query": {},
  "data": {},
  "stats": {},
  "meta": {},
  "error": null
}
```

Typical failure shape:

```json
{
  "ok": false,
  "summary": "Unsupported market_type: options",
  "error": {
    "code": "UNSUPPORTED_MARKET_TYPE",
    "message": "Unsupported market_type: options",
    "context": {
      "method": "fetch_ticker",
      "retryable": false
    }
  }
}
```

## Guidance For The Agent

- Normalize symbols to ccxt style like `BTC/USDT` when possible.
- Prefer `spot` unless the user explicitly asks for `swap` or `future`.
- Keep scanner universes conservative because public APIs are rate-limited.
- If a command returns `ok=false` and `retryable=true`, retry once with smaller scope before escalating.
- If the user only wants a short answer, summarize from `summary` and `highlights` instead of dumping raw JSON.
