# Loop Constraints

> Add rules below with `/constraints <rule>` in your agent.
> The `loop-constraints` skill reads this file at the start of every run.
> Constraints here are **binding** — the agent MUST follow them.

## Push & Merge
- Don't push before telling me
- Never auto-merge to main without human approval
- Always create a draft PR first; let me review before marking ready

## Paths
- Never edit .env, .env.*, auth/, payments/, secrets/, credentials/
- Never edit wallet/, exchange/, keys/, or any file with api keys / seeds
- Never edit infrastructure configs without human approval
- Never place, cancel, or size live trading orders

## Trading scope
- Only BTC and ETH crypto futures, intraday (see docs/trading-brief.md)
- Pattern: **крючки (hooks)** — long AND short; full rules in docs/trading-brief.md
- Timeframes: context 4h + 1h, entry on 15m; do not invent other TFs or patterns
- Long: uptrend/HH-HL → 1–3 red pullback → long on red hook close → SL under hook low → min R:R 1:2–1:3
- Short: downtrend/LH-LL → 1–3 green pullback → short on green hook close → SL above hook high → min R:R 1:2–1:3
- Fail closed on ambiguous bias or dual long+short setup on same bar
- Do not invent other assets, swing/position holds, or extra patterns without human update to trading-brief.md
- Paper/sim only until human explicitly enables live
- Never place, cancel, or size live orders; never auto-trade from loops
- Never change risk %, leverage, or max positions without human approval in trading-brief.md

## Code
- Always run tests before proposing a fix
- Never disable tests to make CI green
- Never refactor unrelated code — one fix per run
- Max 3 fix attempts per item; escalate after
- Enforce the attempt limit mechanically: log each try to `loop-ledger.json` and run `loop-context --check` before retrying (see the `loop-guard` skill)

## Communication
- Always tell me what you're about to do before doing it
- Never close an issue or PR without my approval

## Budget
- If token spend hits 80% of daily cap, switch to report-only
- If loop-pause-all is active, exit immediately

---
<!-- Add your own rules below. Use plain English. The loop reads this verbatim. -->
