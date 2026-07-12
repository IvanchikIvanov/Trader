# Trading Brief — Trader

> Living doc. Source of truth for strategy + risk.  
> Agents must follow this with `loop-constraints.md`. Do not invent rules.

## Status

| Field | Value |
|-------|--------|
| Mode | **Paper first** (no live keys in repo / loops) |
| Stage | Pattern **крючки (hooks)** specified — risk numbers still TBD |
| Last updated | 2026-07-13 |

## Markets & instruments

| | |
|--|--|
| **Asset class** | Crypto **futures** |
| **Symbols** | **BTC** and **ETH** (e.g. BTCUSDT / ETHUSDT perps — venue TBD) |
| **Style** | **Intraday** |
| **Venue** | TBD |

## Timeframes

| Role | TF |
|------|-----|
| Context / trend | **4h**, **1h** |
| Setup / entry candle | **15m** (primary for hook candle; confirm with higher TF bias) |

Use higher TF (1h/4h) to confirm **uptrend**; execute hook logic primarily on **15m** unless human says otherwise.

---

## Pattern name

**Крючки (Hooks)** — long continuation after a shallow pullback in an uptrend.

### Core idea

1. Find **ascending** price action.  
2. After a **new high**, wait for a **small pullback down** (the hook).  
3. Enter **long on close** of that red pullback candle.  
4. Goal: catch **trend continuation**.

---

## Long setup — step by step

### 1. Direction filter (bias)

Price must be in an **uptrend**, or after a **clear turn up**.

Evidence:

- Higher highs (HH) and higher lows (HL), or  
- Clear bullish structure after a bottoming reversal  

If trend is down or unclear → **no long hooks**.

Higher TF (1h / 4h) should not contradict: prefer longs only when 1h/4h bias is up or neutralizing into up.

### 2. Form the hook

After price prints a **new high** and pushes up:

| Rule | Spec |
|------|------|
| Pullback | Price starts correcting **down** |
| Hook length | **1–3 consecutive red candles** |
| Hook candle | The **last** (or only) **red** candle of that pullback = **the hook** |

Notes:

- Green candles inside the pullback that break the “1–3 red” simplicity → treat carefully; default is **only pure 1–3 red** pullbacks.  
- Hook is defined on the **entry TF (15m)** unless specified otherwise.

### 3. Entry (long)

| | |
|--|--|
| Trigger | **Close** of the hook candle (close of the red pullback candle) |
| Order | **Market** at close, or **limit** at that close price |
| Side | **Long only** for this pattern (short hook rules not defined yet) |

No entry:

- Before the hook candle **closes**  
- If more than **3** red candles already (pullback too deep / not a hook)  
- If pullback is not red-candle based as defined  

### 4. Stop-loss

| | |
|--|--|
| Placement | **Below the hook low** (below the low of the red hook candle) |
| Buffer | Optional small buffer under that low (“air”) — size TBD in risk config |
| Invalidation | Price **breaks below hook low** → structure broken → full exit |

### 5. Take-profit & exit

| Exit type | Rule |
|-----------|------|
| Min R:R | Target at least **1:2** or **1:3** vs stop distance |
| Partial | Optional scale-out at nearest **resistance** |
| Hard fail | Full exit if price **breaks hook low** to the downside |
| Trail | Optional trailing using **new higher lows** as structure advances |

---

## Formal decision checklist (long)

Use this in detectors / tests:

```
[ ] 1h and/or 4h bias: uptrend or clear bullish turn
[ ] On 15m: recent new high (HH) in the impulse
[ ] Pullback = 1..3 consecutive red candles after that impulse
[ ] Current bar is the last red of that pullback and has CLOSED
[ ] Entry long at close (market) or limit @ close
[ ] SL under hook candle low (− optional buffer)
[ ] TP plan: min 1:2 or 1:3; optional partial @ resistance; trail HL
[ ] Exit all if low of hook is broken
```

Fail closed: if any box is false → **no trade**.

---

## Anti-patterns (do NOT take)

- Counter-trend hooks in a clear **downtrend**  
- Pullback of **4+** red candles (not a “small” hook)  
- Entry **before** hook candle close (wick chasing mid-bar)  
- Hook that is not a red close (doji / green “pullback” without defined rules)  
- No prior **new high** / impulse — random red candle is not a hook  
- Overnight hold of a failed structure without human rule (intraday mandate)

---

## Risk (still open — fill before live / size logic)

| Rule | Value | Status |
|------|--------|--------|
| Risk per trade | TBD % of equity | **open** |
| SL buffer under hook low | TBD ticks/% | **open** |
| Prefer R:R | **1:2 min**, prefer **1:3** | set |
| Max concurrent positions | TBD (BTC/ETH) | **open** |
| Max daily drawdown → stop day | TBD | **open** |
| Max leverage | TBD | **open** |
| Side | **Long hooks only** for now | set |
| Flat by session end | Yes (intraday) — TZ TBD | open |

---

## Execution policy

| | |
|--|--|
| Paper / live | **Paper / sim only** until human enables live |
| Auto-order from loops | **Never** |
| Live API keys in git / STATE | **Never** |
| Human gate | Live enable, leverage, risk %, buffer size |

---

## Implementation sketch (for future code)

Suggested modules (do not invent extra edge):

1. **Market data** — OHLCV 15m / 1h / 4h for BTC & ETH  
2. **Trend filter** — HH/HL or structure on 1h/4h  
3. **Hook detector** — after local HH, count 1–3 red closes; mark hook candle  
4. **Signal** — long at hook close; SL = hook.low − buffer; TP = entry + k×R  
5. **Risk gate** — size from risk%; block if daily DD / max positions hit  
6. **Paper broker** — fill market/limit; log trades  
7. **Exits** — TP hit, partial resistance, trail HL, or hook low break  

Tests: fixture candles for valid hook, 4-red reject, counter-trend reject, pre-close reject.

---

## Open questions for human

1. Exchange (Binance / Bybit / …) and contract (USDT-M perp)?  
2. Risk % per trade and max leverage?  
3. Exact SL buffer (ticks or %)?  
4. Session timezone / “flat by when”?  
5. Short side: mirror “крючки” down later?  
6. Must **all** of 15m+1h+4h agree, or is 15m enough if 1h up?  

---

## Changelog

| Date | Change |
|------|--------|
| 2026-07-13 | Assets BTC/ETH futures intraday; pattern **крючки** long rules locked |
