# AGENTS.md

## Project

Trader — loop-engineering multi-pattern workspace (Grok primary).

## Test commands

```bash
# Fill in when the app exists:
# npm test
# npm run lint
# pytest
```

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
