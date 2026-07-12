# Loop Budget — Trader

> All patterns scaffolded. **Week one: L1 only.** High-cadence loops (PR / CI) stay off or 1–2 manual runs until CI exists.

## Daily limits

| Loop | Max runs/day | Max tokens/day | Max sub-agent spawns/run | Notes |
|------|--------------|----------------|--------------------------|-------|
| Daily Triage | 2 | 100k | 0 (L1) / 2 (L2) | Start here |
| Issue Triage | 4 | 80k | 0 / 1 | Pair with Daily Triage |
| Changelog Drafter | 2 | 100k | 0 / 1 | Draft only |
| Post-Merge Cleanup | 2 | 200k | 0 / 2 | Off-peak |
| Dependency Sweeper | 2 | 500k | 0 / 2 | L1 report first |
| PR Babysitter | 0 until PR flow exists | 2M | 0 / 2 | High cost — early-exit required |
| CI Sweeper | 0 until CI exists | 1M | 0 / 2 | Very high cost — enable last |

## Project-wide caps

| Cap | Value |
|-----|-------|
| Total tokens/day (all loops) | 300k (week one) → raise only after audit |
| Concurrent scheduled loops | 2 (prefer Daily + Issue) |
| Max fix attempts per item | 3 then escalate |

## On budget exceed

1. Pause schedulers (`scheduler_delete` / disable automations)  
2. Append event to `loop-run-log.md`  
3. Notify human via `STATE.md` High Priority  

## Kill switch

- Label / command: `loop-pause-all`  
- Resume only after human clears the flag in `STATE.md`  

## Estimate spend

```bash
npx @cobusgreyling/loop-cost --pattern daily-triage --level L1 --cadence 1d
npx @cobusgreyling/loop-cost --pattern pr-babysitter --level L1 --cadence 15m
npx @cobusgreyling/loop-cost --pattern ci-sweeper --level L1 --cadence 15m
```
