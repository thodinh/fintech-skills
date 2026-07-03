---
name: finance-market-skills
description: "Use when the user asks for crypto token prices, ticker data, OHLCV candles, order books, trades, technical indicators, or market scans powered by ccxt."
allowed-tools: Bash(/workspace/scripts/run-tool.sh:*), Bash(./workspace/scripts/run-tool.sh:*)
---

# Finance Market

Use this Skill when you need a strong finance toolset for crypto market data. It wraps the local `finance_market_skills` package through the repo-local wrapper and returns structured JSON that is friendly for AI agents:

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

## Runtime

```bash
bash /workspace/scripts/run-tool.sh --help
```

The runtime is self-contained inside this repo:

- `vendor/` contains the bundled exchange library stack
- `src/` contains the `finance_market_skills` package
- `/workspace/scripts/run-tool.sh` injects both paths into `PYTHONPATH`
- `./workspace/scripts/run-tool.sh` is kept as a compatibility shim when the agent is already running from the repo root

Use exactly one of these commands:

```bash
bash /workspace/scripts/run-tool.sh --help
./workspace/scripts/run-tool.sh --help
```

Always prefer `bash /workspace/scripts/run-tool.sh ...` because it works regardless of the current working directory.

## Core Commands

### Price / Ticker

```bash
bash /workspace/scripts/run-tool.sh get-price --exchange binance --symbol BTC/USDT --pretty
bash /workspace/scripts/run-tool.sh get-ticker --exchange bybit --symbol ETH/USDT --market-type spot --pretty
```

### OHLCV / Order Book / Trades

```bash
bash /workspace/scripts/run-tool.sh get-ohlcv --exchange binance --symbol BTC/USDT --timeframe 1h --limit 200 --series-tail-size 120 --pretty
bash /workspace/scripts/run-tool.sh get-orderbook --exchange okx --symbol SOL/USDT --limit 50 --pretty
bash /workspace/scripts/run-tool.sh get-trades --exchange bybit --symbol BTC/USDT --limit 100 --pretty
```

### Indicators

```bash
bash /workspace/scripts/run-tool.sh compute-indicators \
  --exchange binance \
  --symbol BTC/USDT \
  --timeframe 1h \
  --indicators rsi,macd,bbands,ema_20 \
  --indicator-params-json '{"ema_20":{"period":20},"bbands":{"period":20,"stddev":2.0}}' \
  --pretty
```

### Scanners

```bash
bash /workspace/scripts/run-tool.sh scan-top-movers --exchange binance --quote USDT --top-n 10 --pretty
bash /workspace/scripts/run-tool.sh scan-volume-spikes --exchange binance --quote USDT --timeframe 1h --lookback 48 --spike-factor 3 --pretty
bash /workspace/scripts/run-tool.sh scan-volatility-rank --exchange okx --quote USDT --timeframe 4h --top-n 10 --pretty
bash /workspace/scripts/run-tool.sh scan-breakouts --exchange bybit --quote USDT --timeframe 1h --rule close>bb_upper --pretty
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
- Never use `python3 -c "import ccxt; ..."` directly, because the bundled runtime is exposed through the wrapper rather than the global Python environment.
- Never rewrite `/workspace/...` into `./workspace/...` unless the agent is already in the repo root and needs the compatibility shim.
- For agent execution, prefer `bash /workspace/scripts/run-tool.sh ...` over `python -m ...` so the runtime does not depend on package installation or `PYTHONPATH`.

## Troubleshooting

- If you see `ModuleNotFoundError: No module named 'finance_market_skills'` or `No module named 'ccxt'`, the wrapper was likely bypassed. Retry with:

```bash
bash /workspace/scripts/run-tool.sh --help
```

- If a market-data command fails because the exchange upstream is unavailable, retry with a smaller scope or a different supported exchange.
- For agent execution, prefer:

```bash
bash /workspace/scripts/run-tool.sh get-price --exchange binance --symbol BTC/USDT --pretty
```

instead of calling `finance-market-skills ...`, `python -m finance_market_skills.cli ...`, or `python3 -c "import ccxt; ..."`.
