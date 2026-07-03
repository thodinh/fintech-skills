# Finance Market Self-Contained Rename Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the project from `finance-market-skills` to `finance-market-skills` / `Finance Market`, vendor full `ccxt`, and make the root skill run without any install step in ephemeral agent sandboxes.

**Architecture:** The implementation renames the Python package to `finance_market_skills`, renames the CLI and skill metadata to `finance-market-skills` / `Finance Market`, and adds a vendored `ccxt` runtime under `vendor/`. The root wrapper script becomes the canonical agent entrypoint by exporting `PYTHONPATH=/workspace/vendor:/workspace/src` so the runtime is fully self-contained.

**Tech Stack:** Python 3.11+, vendored `ccxt`, Bash, pytest

---

## Repo structure after change

- `/workspace/SKILL.md`
- `/workspace/agents/openai.yaml`
- `/workspace/scripts/run-tool.sh`
- `/workspace/vendor/ccxt/`
- `/workspace/src/finance_market_skills/`
- `/workspace/tests/`
- `/workspace/README.md`
- `/workspace/pyproject.toml`

Removed or renamed:

- `/workspace/src/finance_market_skills/` -> `/workspace/src/finance_market_skills/`
- legacy CLI name `finance-market-skills` -> `finance-market-skills`

---

### Task 1: Vendor full `ccxt` into the repository

**Files:**
- Create: `/workspace/vendor/ccxt/`
- Modify: `/workspace/scripts/run-tool.sh`

- [ ] **Step 1: Create the vendor directory**

Run:

```bash
mkdir -p /workspace/vendor
```

Expected: the directory exists with no error.

- [ ] **Step 2: Vendor the full `ccxt` package source into `/workspace/vendor/ccxt`**

Use the local environment if `ccxt` is already installed; otherwise obtain the exact source tree and place it at:

```text
/workspace/vendor/ccxt
```

The vendored tree must include the package modules needed by normal `import ccxt`.

- [ ] **Step 3: Update the root wrapper so vendored dependencies are always on `PYTHONPATH`**

Modify `/workspace/scripts/run-tool.sh` to:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/vendor:${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

exec python -m finance_market_skills.cli "$@"
```

- [ ] **Step 4: Verify the wrapper can see vendored paths**

Run:

```bash
/workspace/scripts/run-tool.sh --help >/tmp/fms-help.txt && test -s /tmp/fms-help.txt && echo ok
```

Expected: prints `ok`

---

### Task 2: Rename the Python package to `finance_market_skills`

**Files:**
- Rename: `/workspace/src/finance_market_skills/` -> `/workspace/src/finance_market_skills/`
- Modify: every Python file under `/workspace/src/finance_market_skills/`
- Modify: `/workspace/tests/*.py`

- [ ] **Step 1: Rename the package directory**

Run:

```bash
mv /workspace/src/finance_market_skills /workspace/src/finance_market_skills
```

Expected: the package now lives under `/workspace/src/finance_market_skills`.

- [ ] **Step 2: Rewrite all internal imports to the new package name**

Examples of required changes:

```python
from finance_market_skills.market_data.ticker import get_ticker
from finance_market_skills.schemas.response import ok_response
from finance_market_skills.indicators.compute import compute_indicators
```

There must be no remaining imports of:

```python
finance_market_skills
```

- [ ] **Step 3: Rewrite test imports to the new package name**

Example:

```python
from finance_market_skills.cli import main
from finance_market_skills.indicators.compute import compute_indicators
```

- [ ] **Step 4: Verify no old package import remains**

Run:

```bash
! grep -R "finance_market_skills" /workspace/src /workspace/tests && echo ok
```

Expected: prints `ok`

---

### Task 3: Rename packaging metadata and console entrypoint

**Files:**
- Modify: `/workspace/pyproject.toml`

- [ ] **Step 1: Update project metadata in `pyproject.toml`**

Replace the old project block values with:

```toml
[project]
name = "finance-market-skills"
version = "0.1.0"
description = "Finance Market self-contained AI-agent toolkit using vendored ccxt"
requires-python = ">=3.11"
dependencies = []
```

Notes:

- `dependencies = []` because runtime no longer depends on external install-time `ccxt`
- keep `pytest` in `optional-dependencies.dev`

- [ ] **Step 2: Rename the console script**

Set:

```toml
[project.scripts]
finance-market-skills = "finance_market_skills.cli:main"
```

- [ ] **Step 3: Update package discovery if needed**

Keep:

```toml
[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 4: Verify the new CLI help works after editable install**

Run:

```bash
python -m pip install -e . --no-deps
finance-market-skills --help >/tmp/fms-cli.txt && test -s /tmp/fms-cli.txt && echo ok
```

Expected: prints `ok`

---

### Task 4: Update the CLI module and runtime entrypoint

**Files:**
- Modify: `/workspace/src/finance_market_skills/cli.py`
- Modify: `/workspace/src/finance_market_skills/__init__.py`

- [ ] **Step 1: Update all imports in `cli.py` to the new package**

Example:

```python
from finance_market_skills import (
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
```

- [ ] **Step 2: Ensure `__init__.py` re-exports still work under the new package name**

Example:

```python
from finance_market_skills.indicators.compute import compute_indicators
from finance_market_skills.market_data.price import get_price
from finance_market_skills.market_data.ticker import get_ticker
```

- [ ] **Step 3: Verify module import**

Run:

```bash
python -c "import finance_market_skills; print(sorted(finance_market_skills.__all__))"
```

Expected: prints the exported tool names.

---

### Task 5: Update root skill metadata and naming

**Files:**
- Modify: `/workspace/SKILL.md`
- Modify: `/workspace/agents/openai.yaml`

- [ ] **Step 1: Rename the skill code in `SKILL.md`**

Set the frontmatter header to:

```md
---
name: finance-market-skills
description: "Use when the user asks for token prices, OHLCV candles, order books, trades, indicators, or market scans powered by a self-contained Finance Market runtime."
allowed-tools: Bash(finance-market-skills:*), Bash(/workspace/scripts/run-tool.sh:*)
---
```

- [ ] **Step 2: Update display-facing content in `SKILL.md`**

Use `Finance Market` in the title and user-facing narrative. Remove wording that implies an install step is required for agent runtime.

- [ ] **Step 3: Update `agents/openai.yaml`**

Set:

```yaml
interface:
  display_name: "Finance Market"
  short_description: "Get token prices, indicators, and market scans"
  default_prompt: "Use $finance-market-skills to fetch market data, compute indicators, and run market scans with the self-contained Finance Market runtime."
```

- [ ] **Step 4: Verify naming consistency**

Run:

```bash
grep -n "finance-market-skills\\|Finance Market" /workspace/SKILL.md /workspace/agents/openai.yaml
```

Expected: all references use the new names.

---

### Task 6: Update README for self-contained runtime and new naming

**Files:**
- Modify: `/workspace/README.md`

- [ ] **Step 1: Rename the project title and user-facing references**

Update README to use `Finance Market` for the skill-facing name and `finance-market-skills` for the CLI.

- [ ] **Step 2: Split agent runtime from local developer install**

Add a section similar to:

```md
## Agent Runtime

The root skill is self-contained and uses `/workspace/scripts/run-tool.sh`, so the agent does not need to install dependencies before use.

## Developer Install

If you want a local editable CLI for development:

```bash
python -m pip install -e . --no-deps
```
```

- [ ] **Step 3: Update command examples**

Examples must use:

```bash
finance-market-skills get-price --exchange binance --symbol BTC/USDT --pretty
/workspace/scripts/run-tool.sh get-price --exchange binance --symbol BTC/USDT --pretty
```

- [ ] **Step 4: Verify no old public name remains**

Run:

```bash
! grep -n "Finance Market\\|finance-market-skills" /workspace/README.md && echo ok
```

Expected: prints `ok`

---

### Task 7: Rewrite tests for new package and CLI names

**Files:**
- Modify: all `/workspace/tests/*.py`

- [ ] **Step 1: Update import paths in every test**

Examples:

```python
from finance_market_skills.cli import main
from finance_market_skills.indicators.rsi import rsi_series
from finance_market_skills.scanners.breakouts import scan_breakouts
```

- [ ] **Step 2: Update monkeypatch target strings**

Examples:

```python
monkeypatch.setattr("finance_market_skills.cli.get_ticker", fake_get_ticker)
monkeypatch.setattr("finance_market_skills.indicators.compute.get_ohlcv", fake_get_ohlcv)
monkeypatch.setattr("finance_market_skills.scanners.breakouts.compute_indicators", fake_compute_indicators)
```

- [ ] **Step 3: Add one self-contained wrapper smoke test**

Create or extend a test with logic equivalent to:

```python
from pathlib import Path


def test_root_wrapper_exists():
    assert Path("/workspace/scripts/run-tool.sh").exists()
```

- [ ] **Step 4: Run the test suite**

Run:

```bash
pytest -q
```

Expected: PASS

---

### Task 8: Final verification for self-contained runtime

**Files:**
- Verify: `/workspace/scripts/run-tool.sh`
- Verify: `/workspace/SKILL.md`
- Verify: `/workspace/README.md`
- Verify: `/workspace/vendor/ccxt/`

- [ ] **Step 1: Verify wrapper from a non-root `cwd`**

Run:

```bash
cd /tmp && /workspace/scripts/run-tool.sh --help >/tmp/fms-wrapper.txt && test -s /tmp/fms-wrapper.txt && echo ok
```

Expected: prints `ok`

- [ ] **Step 2: Verify the new package imports without install-time `ccxt` dependency**

Run:

```bash
PYTHONPATH=/workspace/vendor:/workspace/src python -c "import ccxt, finance_market_skills; print('ok')"
```

Expected: prints `ok`

- [ ] **Step 3: Run compile checks**

Run:

```bash
python -m compileall src tests
```

Expected: completes without syntax errors.

- [ ] **Step 4: Verify no legacy package name remains in active source/docs**

Run:

```bash
! grep -R "finance_market_skills" /workspace/src /workspace/tests /workspace/SKILL.md /workspace/README.md && echo ok
```

Expected: prints `ok`

---

## Plan self-review checklist

- Covers spec sections: full vendor `ccxt`, package rename, CLI rename, wrapper runtime, metadata rename, docs updates, test rewrite, self-contained verification.
- No placeholders or references to undefined tasks remain.
- New names are consistent: `finance-market-skills`, `Finance Market`, `finance_market_skills`.

## Execution handoff

Plan complete and saved to `/workspace/docs/superpowers/plans/2026-07-03-finance-market-self-contained-rename.md`. Two execution options:

1. Subagent-Driven (recommended) — I dispatch a fresh subagent per task, review between tasks
2. Inline Execution — execute tasks in this session using executing-plans, with checkpoints

Which approach?
