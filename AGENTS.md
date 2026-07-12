# AGENTS.md

## Project

Trader — loop-engineering multi-pattern workspace (Grok primary).

## Test commands

```bash
python -m pip install -r requirements.txt
# If machine has broken pytest plugins (web3): set PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"   # PowerShell
python -m pytest tests/ -q
$env:PYTHONPATH = "src"
python -m trader backtest --symbol BTCUSDT --days 30
```

Paper only — no live orders. Strategy rules: `docs/trading-brief.md`.

## Loop conventions

- **Week one: L1 report-only** for every pattern — see `LOOP.md`
- Read `loop-constraints.md` at the start of every loop run
- Read/update the pattern's state file; never invent work outside High Priority
- No auto-merge; draft PRs only
- Max 3 fix attempts → escalate via `loop-ledger.json` + `loop-context --check`
- Never touch denylist paths (secrets, wallet, exchange keys, `.env*`)
- Append runs to `loop-run-log.md`; respect `loop-budget.md`

## Pattern → state

| Pattern | State file |
|---------|------------|
| daily-triage | `STATE.md` |
| issue-triage | `issue-triage-state.md` |
| pr-babysitter | `pr-babysitter-state.md` |
| ci-sweeper | `ci-sweeper-state.md` |
| dependency-sweeper | `dependency-sweeper-state.md` |
| post-merge-cleanup | `post-merge-state.md` |
| changelog-drafter | `changelog-drafter-state.md` |

## Skills

Grok skills live under `.grok/skills/`. Prefer `loop-triage` for morning signal; pair with `issue-triage`. Use `loop-verifier` before any L2 fix lands. Use `loop-guard` when retrying fixes.
