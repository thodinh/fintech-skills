# Root Skill Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the skill discovery entrypoint to `/workspace/SKILL.md` and normalize all skill assets to root-level paths without changing the crypto toolkit runtime behavior.

**Architecture:** Keep the Python package and CLI unchanged, but move the skill discovery and wrapper assets to root-level files: `SKILL.md`, `agents/openai.yaml`, and `scripts/run-tool.sh`. Remove or deprecate the nested `skills/finance-market-skills/` layout so the repo has one canonical skill entrypoint.

**Tech Stack:** Markdown, YAML, Bash, Python packaging, pytest

---

## Repo structure after change

- `/workspace/SKILL.md`
- `/workspace/agents/openai.yaml`
- `/workspace/scripts/run-tool.sh`
- `/workspace/README.md`
- `/workspace/src/finance_market_skills/` (unchanged runtime)
- `/workspace/tests/test_cli.py` (unchanged unless wrapper path coverage is added)

Deprecated or removed:

- `/workspace/skills/finance-market-skills/SKILL.md`
- `/workspace/skills/finance-market-skills/agents/openai.yaml`
- `/workspace/skills/finance-market-skills/scripts/run-tool.sh`

---

### Task 1: Move skill discovery file to root

**Files:**
- Create: `/workspace/SKILL.md`
- Modify: `/workspace/README.md`

- [ ] **Step 1: Copy the nested skill content into the root skill file**

Create `/workspace/SKILL.md` with this content:

```md
---
name: finance-market-skills
description: "Use when the user asks for crypto token prices, ticker data, OHLCV candles, order books, trades, technical indicators, or market scans powered by ccxt."
allowed-tools: Bash(finance-market-skills:*), Bash(python -m finance_market_skills.cli:*), Bash(./scripts/run-tool.sh:*)
---

# Finance Market

Use this Skill when you need a strong finance toolset for crypto market data. It wraps the local `finance_market_skills` package and returns structured JSON that is friendly for AI agents:

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
finance-market-skills --help
```

or:

```bash
python -m finance_market_skills.cli --help
```

or the repo-local wrapper:

```bash
./scripts/run-tool.sh --help
```

## Core Commands

### Price / Ticker

```bash
finance-market-skills get-price --exchange binance --symbol BTC/USDT --pretty
finance-market-skills get-ticker --exchange bybit --symbol ETH/USDT --market-type spot --pretty
```

### OHLCV / Order Book / Trades

```bash
finance-market-skills get-ohlcv --exchange binance --symbol BTC/USDT --timeframe 1h --limit 200 --series-tail-size 120 --pretty
finance-market-skills get-orderbook --exchange okx --symbol SOL/USDT --limit 50 --pretty
finance-market-skills get-trades --exchange bybit --symbol BTC/USDT --limit 100 --pretty
```

### Indicators

```bash
finance-market-skills compute-indicators \
  --exchange binance \
  --symbol BTC/USDT \
  --timeframe 1h \
  --indicators rsi,macd,bbands,ema_20 \
  --indicator-params-json '{"ema_20":{"period":20},"bbands":{"period":20,"stddev":2.0}}' \
  --pretty
```

### Scanners

```bash
finance-market-skills scan-top-movers --exchange binance --quote USDT --top-n 10 --pretty
finance-market-skills scan-volume-spikes --exchange binance --quote USDT --timeframe 1h --lookback 48 --spike-factor 3 --pretty
finance-market-skills scan-volatility-rank --exchange okx --quote USDT --timeframe 4h --top-n 10 --pretty
finance-market-skills scan-breakouts --exchange bybit --quote USDT --timeframe 1h --rule close>bb_upper --pretty
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
```

- [ ] **Step 2: Update the README so it points to the root skill file**

In `/workspace/README.md`, replace the section:

```md
## Skill Folder

The repo now includes a ready-to-use Skill at [SKILL.md](file:///workspace/skills/finance-market-skills/SKILL.md) with companion metadata at [openai.yaml](file:///workspace/skills/finance-market-skills/agents/openai.yaml).

Local wrapper:

```bash
./skills/finance-market-skills/scripts/run-tool.sh get-price --exchange binance --symbol BTC/USDT --pretty
```
```

with:

```md
## Skill Folder

The repo now includes a ready-to-use root Skill at [SKILL.md](file:///workspace/SKILL.md) with companion metadata at [openai.yaml](file:///workspace/agents/openai.yaml).

Local wrapper:

```bash
./scripts/run-tool.sh get-price --exchange binance --symbol BTC/USDT --pretty
```
```

- [ ] **Step 3: Verify the new root skill file exists**

Run:

```bash
test -f /workspace/SKILL.md && echo ok
```

Expected: prints `ok`

---

### Task 2: Move metadata and wrapper assets to root

**Files:**
- Create: `/workspace/agents/openai.yaml`
- Create: `/workspace/scripts/run-tool.sh`

- [ ] **Step 1: Create root agent metadata**

Create `/workspace/agents/openai.yaml` with:

```yaml
interface:
  display_name: "Finance Market"
  short_description: "Get token prices, indicators, and crypto market scans with ccxt"
  default_prompt: "Use $finance-market-skills to fetch crypto market data, calculate technical indicators, and run market scans with structured JSON output."
```

- [ ] **Step 2: Create root wrapper script**

Create `/workspace/scripts/run-tool.sh` with:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

exec python -m finance_market_skills.cli "$@"
```

- [ ] **Step 3: Make the wrapper executable**

Run:

```bash
chmod +x /workspace/scripts/run-tool.sh
```

Expected: command succeeds with no output.

- [ ] **Step 4: Verify the wrapper help output**

Run:

```bash
./scripts/run-tool.sh --help >/tmp/root-skill-help.txt && test -s /tmp/root-skill-help.txt && echo ok
```

Expected: prints `ok`

---

### Task 3: Remove duplicate nested skill source of truth

**Files:**
- Delete: `/workspace/skills/finance-market-skills/SKILL.md`
- Delete: `/workspace/skills/finance-market-skills/agents/openai.yaml`
- Delete: `/workspace/skills/finance-market-skills/scripts/run-tool.sh`

- [ ] **Step 1: Delete the nested skill files**

Run:

```bash
rm -f /workspace/skills/finance-market-skills/SKILL.md
rm -f /workspace/skills/finance-market-skills/agents/openai.yaml
rm -f /workspace/skills/finance-market-skills/scripts/run-tool.sh
```

Expected: commands succeed with no output.

- [ ] **Step 2: Verify the nested files are gone**

Run:

```bash
test ! -f /workspace/skills/finance-market-skills/SKILL.md && \
test ! -f /workspace/skills/finance-market-skills/agents/openai.yaml && \
test ! -f /workspace/skills/finance-market-skills/scripts/run-tool.sh && echo ok
```

Expected: prints `ok`

---

### Task 4: Run final verification for the root layout

**Files:**
- Modify: `/workspace/README.md`
- Verify: `/workspace/SKILL.md`
- Verify: `/workspace/agents/openai.yaml`
- Verify: `/workspace/scripts/run-tool.sh`

- [ ] **Step 1: Run the Python test suite**

Run:

```bash
pytest -q
```

Expected: PASS

- [ ] **Step 2: Run compile checks**

Run:

```bash
python -m compileall src tests
```

Expected: completes without syntax errors.

- [ ] **Step 3: Verify CLI help still works**

Run:

```bash
finance-market-skills --help >/tmp/root-cli-help.txt && test -s /tmp/root-cli-help.txt && echo ok
```

Expected: prints `ok`

- [ ] **Step 4: Verify README no longer references the nested skill path**

Run:

```bash
! grep -n "skills/finance-market-skills" /workspace/README.md && echo ok
```

Expected: prints `ok`

---

## Plan self-review checklist

- Covers spec sections: root `SKILL.md`, root `agents/openai.yaml`, root `scripts/run-tool.sh`, README path migration, nested path retirement, verification commands.
- No placeholders or indirect references remain.
- Paths are consistent with the approved spec and no runtime behavior of the Python toolkit changes.

## Execution handoff

Plan complete and saved to `/workspace/docs/superpowers/plans/2026-07-03-root-skill-layout.md`. Two execution options:

1. Subagent-Driven (recommended) — I dispatch a fresh subagent per task, review between tasks
2. Inline Execution — execute tasks in this session using executing-plans, with checkpoints

Which approach?
