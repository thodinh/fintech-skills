# LobeHub Installed Skill Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `finance-market-skills` run correctly after a LobeHub-style skill install where the installed skill directory, not the source repo root, is the runtime.

**Architecture:** Treat the installed skill directory as self-contained runtime. Use a repo-root launcher plus `scripts/run-tool.sh`, both resolving paths from their own file locations. Remove `/workspace` as the primary contract from skill docs and allowed commands, keeping documentation focused on relative launchers inside the installed skill directory.

**Tech Stack:** Bash, Python 3.11, vendored `ccxt`, `pytest`

---

### Task 1: Align Skill Contract With Installed Directory Runtime

**Files:**
- Modify: `/workspace/SKILL.md`
- Modify: `/workspace/README.md`

- [ ] **Step 1: Rewrite `SKILL.md` runtime commands to installed-directory launchers**

Replace primary runtime examples with:

```bash
./finance-market-skills --help
./finance-market-skills get-price --exchange binance --symbol BTC/USDT --pretty
bash ./scripts/run-tool.sh --help
```

- [ ] **Step 2: Restrict `allowed-tools` to installed-directory commands**

Use frontmatter commands shaped like:

```md
allowed-tools: Bash(./finance-market-skills:*), Bash(finance-market-skills:*), Bash(./scripts/run-tool.sh:*), Bash(scripts/run-tool.sh:*), Bash(bash ./scripts/run-tool.sh:*), Bash(bash scripts/run-tool.sh:*), Bash(find:*), Bash(pwd:*), Bash(ls:*)
```

- [ ] **Step 3: Update troubleshooting and health-check guidance**

Document:

```bash
pwd
ls
find . -path '*/scripts/run-tool.sh' -o -name 'finance-market-skills'
```

and prefer launcher order:

```bash
./finance-market-skills --help
bash ./scripts/run-tool.sh --help
```

- [ ] **Step 4: Mirror the same installed-skill guidance in `README.md`**

Use the same launcher examples and remove `/workspace` as the recommended path.

- [ ] **Step 5: Commit**

```bash
git add /workspace/SKILL.md /workspace/README.md
git commit -m "docs: target installed skill runtime"
```

### Task 2: Keep Launcher Self-Contained

**Files:**
- Modify: `/workspace/finance-market-skills`
- Modify: `/workspace/scripts/run-tool.sh`

- [ ] **Step 1: Verify launcher resolves root from its own file path**

Launcher pattern:

```bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "${ROOT_DIR}/scripts/run-tool.sh" "$@"
```

- [ ] **Step 2: Verify runtime wrapper resolves root from its own file path**

Wrapper pattern:

```bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/vendor:${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"
exec "${PYTHON_BIN}" -m finance_market_skills.cli "$@"
```

- [ ] **Step 3: Ensure launchers stay executable**

Run:

```bash
chmod +x /workspace/finance-market-skills /workspace/scripts/run-tool.sh
```

- [ ] **Step 4: Commit**

```bash
git add /workspace/finance-market-skills /workspace/scripts/run-tool.sh
git commit -m "fix: keep skill launcher self-contained"
```

### Task 3: Test Installed-Directory Behavior

**Files:**
- Test: `/workspace/tests/test_cli.py`

- [ ] **Step 1: Keep existing CLI regression coverage**

Run:

```bash
PYTHONPATH=/workspace/vendor:/workspace/src python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Smoke-test root launcher from repo root**

Run:

```bash
cd /workspace && ./finance-market-skills --help
```

Expected: CLI help prints successfully.

- [ ] **Step 3: Smoke-test script wrapper from repo root**

Run:

```bash
cd /workspace && bash ./scripts/run-tool.sh --help
```

Expected: CLI help prints successfully.

- [ ] **Step 4: Simulate installed skill directory in a temp path**

Run:

```bash
TMP_DIR="$(mktemp -d)"
cp -R /workspace "$TMP_DIR/installed-skill"
cd "$TMP_DIR/installed-skill" && ./finance-market-skills --help
cd "$TMP_DIR/installed-skill" && bash ./scripts/run-tool.sh --help
```

Expected: both commands print help successfully without referencing `/workspace`.

- [ ] **Step 5: Commit**

```bash
git add /workspace/tests/test_cli.py
git commit -m "test: verify installed skill runtime"
```

### Task 4: Push Final Main Branch State

**Files:**
- Modify: `/workspace/.git` state only

- [ ] **Step 1: Confirm working tree is clean**

Run:

```bash
git status --short --branch
```

Expected: branch `main` with no pending file changes.

- [ ] **Step 2: Push `main`**

Run:

```bash
git push origin main
```

Expected: remote `main` updated or already up to date.
