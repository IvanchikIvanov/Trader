# Trader

Trading-related project scaffolded with [Loop Engineering](https://github.com/cobusgreyling/loop-engineering) for Grok agents.

**→ [Как оптимально использовать](docs/GUIDE.md)** — ежедневный ритуал, L1→L3, бюджет, safety, cheat sheet.

## Loop Engineering

All 7 production patterns are installed (L1 report-only by default).

| Pattern | State | Skill |
|---------|-------|-------|
| Daily Triage | `STATE.md` | `loop-triage` |
| Issue Triage | `issue-triage-state.md` | `issue-triage` |
| PR Babysitter | `pr-babysitter-state.md` | `pr-review-triage` |
| CI Sweeper | `ci-sweeper-state.md` | `ci-triage` |
| Dependency Sweeper | `dependency-sweeper-state.md` | `dependency-triage` |
| Post-Merge Cleanup | `post-merge-state.md` | `post-merge-scan` |
| Changelog Drafter | `changelog-drafter-state.md` | `changelog-scan` |

See **`LOOP.md`** for cadence, human gates, and first commands.

### Quick commands

```bash
# Audit readiness
npx @cobusgreyling/loop-audit . --suggest

# Cost estimate
npx @cobusgreyling/loop-cost --pattern daily-triage --level L1 --cadence 1d

# Circuit breaker (L2+)
npx @cobusgreyling/loop-context --check --ledger loop-ledger.json
```

### First loop (Grok)

```text
/loop 1d Run loop-triage. Update STATE.md. No auto-fix in week one.
```

## Safety

- `docs/safety.md` — denylist, auto-merge policy, trading gates  
- `loop-constraints.md` — binding rules every run  

## License

Private / TBD.
