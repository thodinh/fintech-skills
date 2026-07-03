---
name: finance-market-skills
description: "Use when the user asks for crypto token prices, ticker data, OHLCV candles, order books, trades, technical indicators, or market scans powered by ccxt."
allowed-tools: Bash(./finance-market-skills:*), Bash(finance-market-skills:*), Bash(./scripts/run-tool.sh:*), Bash(scripts/run-tool.sh:*), Bash(bash ./scripts/run-tool.sh:*), Bash(bash scripts/run-tool.sh:*), Bash(find:*), Bash(pwd:*), Bash(ls:*)
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
./finance-market-skills --help
```

The runtime is self-contained inside this repo:

- `vendor/` contains the bundled exchange library stack
- `src/` contains the `finance_market_skills` package
- `scripts/run-tool.sh` injects both paths into `PYTHONPATH`
- `finance-market-skills` at the repo root is the preferred launcher because it resolves relative to the repo itself

Preferred commands when the agent is already in the repo root:

```bash
./finance-market-skills --help
bash ./scripts/run-tool.sh --help
```

## Health Check

Before the first real command in an unfamiliar sandbox, resolve the launcher that actually exists:

```bash
pwd
ls
find . -path '*/scripts/run-tool.sh' -o -name 'finance-market-skills'
```

Then prefer the first working option in this order:

1. `./finance-market-skills --help`
2. `bash ./scripts/run-tool.sh --help`
3. If neither exists, the skill was likely installed incorrectly

This contract assumes the installed skill directory itself is the runtime.

## Core Commands

### Price / Ticker

```bash
./finance-market-skills get-price --exchange binance --symbol BTC/USDT --pretty
./finance-market-skills get-ticker --exchange bybit --symbol ETH/USDT --market-type spot --pretty
```

### OHLCV / Order Book / Trades

```bash
./finance-market-skills get-ohlcv --exchange binance --symbol BTC/USDT --timeframe 1h --limit 200 --series-tail-size 120 --pretty
./finance-market-skills get-orderbook --exchange okx --symbol SOL/USDT --limit 50 --pretty
./finance-market-skills get-trades --exchange bybit --symbol BTC/USDT --limit 100 --pretty
```

### Indicators

```bash
./finance-market-skills compute-indicators \
  --exchange binance \
  --symbol BTC/USDT \
  --timeframe 1h \
  --indicators rsi,macd,bbands,ema_20 \
  --indicator-params-json '{"ema_20":{"period":20},"bbands":{"period":20,"stddev":2.0}}' \
  --pretty
```

### Scanners

```bash
./finance-market-skills scan-top-movers --exchange binance --quote USDT --top-n 10 --pretty
./finance-market-skills scan-volume-spikes --exchange binance --quote USDT --timeframe 1h --lookback 48 --spike-factor 3 --pretty
./finance-market-skills scan-volatility-rank --exchange okx --quote USDT --timeframe 4h --top-n 10 --pretty
./finance-market-skills scan-breakouts --exchange bybit --quote USDT --timeframe 1h --rule close>bb_upper --pretty
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
- Prefer `./finance-market-skills ...` or `bash ./scripts/run-tool.sh ...` when the repo root is available as the current directory.
- For agent execution, prefer the repo-local launchers over `python -m ...` so the runtime does not depend on package installation or global `PYTHONPATH`.

## Troubleshooting

- If you see `ModuleNotFoundError: No module named 'finance_market_skills'` or `No module named 'ccxt'`, the wrapper was likely bypassed. Retry with:

```bash
./finance-market-skills --help
```

- If `./finance-market-skills` is not found, run the health check above and try `bash ./scripts/run-tool.sh --help`.
- If a market-data command fails because the exchange upstream is unavailable, retry with a smaller scope or a different supported exchange.
- For agent execution, prefer:

```bash
./finance-market-skills get-price --exchange binance --symbol BTC/USDT --pretty
```

instead of calling `finance-market-skills ...`, `python -m finance_market_skills.cli ...`, or `python3 -c "import ccxt; ..."`.
