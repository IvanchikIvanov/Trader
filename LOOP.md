# Loop Configuration — Trader

Multi-pattern loop engineering setup (Grok). **Week one: L1 report-only for all loops.** No auto-fix, no auto-merge.

## Active Loops

| Pattern | Cadence | Level | State file | Primary skill | First command |
|---------|---------|-------|------------|---------------|---------------|
| Daily Triage | 1d | L1 report-only | `STATE.md` | `loop-triage` | `/loop 1d Run loop-triage. Update STATE.md. No auto-fix.` |
| Issue Triage | 2h–1d | L1 propose-only | `issue-triage-state.md` | `issue-triage` | `/loop 2h Run issue-triage. Propose labels only. No auto-apply.` |
| PR Babysitter | 10–15m | L1 watch | `pr-babysitter-state.md` | `pr-review-triage` | `/loop 15m Run pr-review-triage. Update state. No auto-merge.` |
| CI Sweeper | 15m | L1 report | `ci-sweeper-state.md` | `ci-triage` | `/loop 15m Run ci-triage on failing CI. Report only. No auto-fix.` |
| Dependency Sweeper | 1d | L1 report | `dependency-sweeper-state.md` | `dependency-triage` | `/loop 1d Run dependency-triage. Report only. Escalate majors.` |
| Post-Merge Cleanup | 1d | L1 report | `post-merge-state.md` | `post-merge-scan` | `/loop 1d Run post-merge-scan. Ticket large debt. No auto-fix.` |
| Changelog Drafter | 1d / on tag | L1 draft | `changelog-drafter-state.md` | `changelog-scan` + `draft-release-notes` | `/loop 1d Run changelog-scan. Draft RELEASE_NOTES_DRAFT.md. Human review only.` |

## Recommended enable order

1. **Daily Triage** + **Issue Triage** — low risk, learn the discipline  
2. **Changelog Drafter** — draft-only, almost free  
3. **Post-Merge Cleanup** — after real merges exist  
4. **Dependency Sweeper** — L1 report, then L2 patch-only with verifier  
5. **PR Babysitter** — when you have open PRs (high token cost)  
6. **CI Sweeper** — last; very high token cost; needs green-ish CI history  

Disable high-frequency loops until the repo has real CI and PRs.

## Human Gates (all patterns)

- No push / merge / force-push without human  
- Security, auth, payments, secrets, infra — always escalate  
- Trading keys, wallet, exchange credentials, `.env*` — never auto-edit  
- Max 3 fix attempts per item → escalate (`loop-ledger.json` + `loop-context --check`)  
- Dependency majors / high-sev CVEs — human only  
- Draft PR only; never auto-merge to main  

## Budget & kill switch

- Caps: see `loop-budget.md`  
- Constraints: `loop-constraints.md` (binding)  
- Safety: `docs/safety.md`  
- Ledger / circuit breaker: `loop-ledger.json`  
  ```bash
  npx @cobusgreyling/loop-context --check --ledger loop-ledger.json
  ```  
- Kill switch: `loop-pause-all` — pause all schedulers, note in `STATE.md` High Priority  

## Worktrees (L2+)

Isolated fix attempts for PR Babysitter / CI Sweeper / Dependency Sweeper:

```bash
npx @cobusgreyling/loop-worktree create --run-id <id> --pattern <pattern>
npx @cobusgreyling/loop-worktree mark --run-id <id> --status rejected
npx @cobusgreyling/loop-worktree cleanup --older-than 24h
```

## Skills map (Grok)

| Skill | Role |
|-------|------|
| `loop-triage` | Morning / daily signal |
| `issue-triage` | Issue queue health |
| `pr-review-triage` | PR shepherding |
| `ci-triage` | Failing CI classification |
| `dependency-triage` | Dep + vuln scan |
| `post-merge-scan` | Debt after merges |
| `changelog-scan` / `draft-release-notes` | Release notes draft |
| `minimal-fix` | Small allowlisted fixes (L2+) |
| `loop-verifier` | Maker/checker verify |
| `loop-guard` | Circuit breaker |
| `loop-budget` | Spend check start/end |
| `loop-constraints` | Read constraints every run |

## Audit & cost

```bash
npx @cobusgreyling/loop-audit . --suggest
npx @cobusgreyling/loop-cost --pattern daily-triage --level L1 --cadence 1d
npx @cobusgreyling/loop-sync .
```

## Links

- Patterns registry: `patterns/registry.yaml`  
- Reference: https://github.com/cobusgreyling/loop-engineering  
- Showcase: https://cobusgreyling.github.io/loop-engineering/  
