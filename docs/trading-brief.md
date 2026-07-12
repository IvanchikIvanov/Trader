# Trading Brief — Trader

> Living doc. Source of truth for strategy + risk.  
> Agents must follow this with `loop-constraints.md`. Do not invent rules.

## Status

| Field | Value |
|-------|--------|
| Mode | **Paper first** (no live keys in repo / loops) |
| Stage | Pattern **крючки (hooks)** long **+ short** locked — risk numbers still TBD |
| Last updated | 2026-07-13 |

## Markets & instruments

| | |
|--|--|
| **Asset class** | Crypto (futures preferred for bot; spot possible for manual) |
| **Core symbols (bot v0)** | **BTC** and **ETH** USDT-M perps |
| **Manual / cases** | **SYN 1H**, **HYPEUSDT 4H** (Bybit) — same hook logic; see `docs/cases/` |
| **Style** | Intraday on 15m (BTC/ETH); higher-TF hooks (1H) allowed when you mark them |
| **Venue** | TBD |
| **Sides** | **Long hooks** and **short hooks** |

## Timeframes

| Role | TF |
|------|-----|
| Context / trend | **4h**, **1h** (and weekly when the hook candle *is* weekly context) |
| Setup / entry candle (bot default) | **15m** on BTC/ETH |
| Setup / entry (manual alts) | Often **1H** — same structure: impulse → opposite-color pullback → enter on close |

Use higher TF for **bias**. Entry TF is where the **hook candle** lives (15m *or* 1H — you choose; bot currently scans 15m).

### Pattern language (how you describe a long hook)

Same idea whether SYN 1H or BTC 15m:

1. **Impulse** — strong green (new high / large up bar).  
2. **Hook** — red pullback candle after that impulse.  
3. **Entry** — only on **close** of the red (not mid-candle).  
4. **Stop** — under red low (+ optional air).  
5. **Target** — fixed levels and/or min **1:2–1:3** R:R.  

**Your version vs “classic shallow Ross hook”:**  
Deep pullbacks (**~30–40% of impulse**) can still be valid if structure is impulse → red close. Do not auto-reject only because the retrace is deep — mark gold/reject by eye, then tune filters.

Example write-ups:

- [`docs/cases/syn-1h-long-hook.md`](cases/syn-1h-long-hook.md)  
- [`docs/cases/hypeusdt-4h-long-hook.md`](cases/hypeusdt-4h-long-hook.md) — clean long hook + follow-through (agent gold structure)

---

## Pattern name

**Крючки (Hooks)** — trend continuation after a shallow counter-move pullback.

| Side | Idea |
|------|------|
| **Long** | Uptrend → new high → small red pullback (hook) → long on red close |
| **Short** | Downtrend → new low → small green pullback (hook) → short on green close |

Both sides share the same R:R, candle-count, and “enter on close only” discipline.

---

## Symmetry cheat sheet

| | Long hook | Short hook |
|--|-----------|------------|
| Trend | Up (HH/HL) or clear turn up | Down (LH/LL) or clear turn down |
| Impulse | New **high** | New **low** |
| Pullback | 1–3 **red** candles | 1–3 **green** candles |
| Hook candle | Last/only **red** of pullback | Last/only **green** of pullback |
| Entry | Close of hook (market / limit @ close) | Same |
| Stop | **Below** hook **low** (+ optional air) | **Above** hook **high** (+ optional air) |
| Min target | 1:2 or 1:3 vs stop | Same |
| Partial | Nearest **resistance** | Nearest **support** |
| Structure break | Break **below** hook low → full exit | Break **above** hook high → full exit |
| Trail | New **higher lows** | New **lower highs** |

---

## Long setup — step by step

### Core idea (long)

1. Find **ascending** price action.  
2. After a **new high**, wait for a **small pullback down** (the hook).  
3. Enter **long on close** of that red pullback candle.  
4. Goal: catch **uptrend continuation**.

### 1. Direction filter (bias)

Price must be in an **uptrend**, or after a **clear turn up**.

Evidence:

- Higher highs (HH) and higher lows (HL), or  
- Clear bullish structure after a bottoming reversal  

If trend is down or unclear → **no long hooks**.

Higher TF (1h / 4h): prefer longs only when bias is up or neutralizing into up.

### 2. Form the long hook

After price prints a **new high** and pushes up:

| Rule | Spec |
|------|------|
| Pullback | Price starts correcting **down** |
| Hook length | **1–3 consecutive red candles** |
| Hook candle | The **last** (or only) **red** candle of that pullback = **the hook** |

Default: **only pure 1–3 red** pullbacks. Hook on **15m** unless specified otherwise.

### 3. Entry (long)

| | |
|--|--|
| Trigger | **Close** of the red hook candle |
| Order | **Market** at close, or **limit** at that close price |
| Side | **Long** |

No entry: before close; 4+ red candles; not a defined red pullback.

### 4. Stop-loss (long)

| | |
|--|--|
| Placement | **Below the hook low** |
| Buffer | Optional small air under that low — size TBD |
| Invalidation | Break **below** hook low → full exit |

### 5. Take-profit & exit (long)

| Exit type | Rule |
|-----------|------|
| Min R:R | **1:2** or **1:3** vs stop distance |
| Partial | Optional at nearest **resistance** |
| Hard fail | Break of hook **low** |
| Trail | Optional trailing on new **higher lows** |

### Checklist (long)

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

Fail closed → **no trade**.

---

## Short setup — step by step

### Core idea (short)

1. Find **descending** price action.  
2. After a **new low**, wait for a **small pullback up** (the hook).  
3. Enter **short on close** of that green pullback candle.  
4. Goal: catch **downtrend continuation**.

### 1. Direction filter (bias)

Price must be in a **downtrend**, or after a **clear turn down**.

Evidence:

- Lower highs (LH) and lower lows (LL), or  
- Clear bearish structure after a topping reversal  

If trend is up or unclear → **no short hooks**.

Higher TF (1h / 4h): prefer shorts only when bias is down or neutralizing into down.

### 2. Form the short hook

After price prints a **new low** and pushes down:

| Rule | Spec |
|------|------|
| Pullback | Price starts correcting **up** |
| Hook length | **1–3 consecutive green candles** |
| Hook candle | The **last** (or only) **green** candle of that pullback = **the short hook** |

Default: **only pure 1–3 green** pullbacks. Hook on **15m** unless specified otherwise.

### 3. Entry (short)

| | |
|--|--|
| Trigger | **Close** of the green hook candle |
| Order | **Market** at close, or **limit** at that close price |
| Side | **Short** |

No entry: before close; 4+ green candles; not a defined green pullback.

### 4. Stop-loss (short)

| | |
|--|--|
| Placement | **Above the hook high** |
| Buffer | Optional small air above that high — size TBD |
| Invalidation | Break **above** hook high → full exit |

### 5. Take-profit & exit (short)

| Exit type | Rule |
|-----------|------|
| Min R:R | **1:2** or **1:3** vs stop distance |
| Partial | Optional at nearest **support** |
| Hard fail | Break of hook **high** |
| Trail | Optional trailing on new **lower highs** |

### Checklist (short)

```
[ ] 1h and/or 4h bias: downtrend or clear bearish turn
[ ] On 15m: recent new low (LL) in the impulse
[ ] Pullback = 1..3 consecutive green candles after that impulse
[ ] Current bar is the last green of that pullback and has CLOSED
[ ] Entry short at close (market) or limit @ close
[ ] SL above hook candle high (+ optional buffer)
[ ] TP plan: min 1:2 or 1:3; optional partial @ support; trail LH
[ ] Exit all if high of hook is broken
```

Fail closed → **no trade**.

---

## Anti-patterns (do NOT take)

### Both sides

- Entry **before** hook candle **close**  
- Pullback of **4+** candles of the pullback color  
- Random candle without prior impulse (no new high for long / no new low for short)  
- Overnight hold of broken structure without human rule (intraday)  
- Trading **against** higher-TF bias (long in clear downtrend / short in clear uptrend)

### Long-specific

- Long hook in clear **downtrend**  
- “Hook” that is not a **red** close as defined  

### Short-specific

- Short hook in clear **uptrend**  
- “Hook” that is not a **green** close as defined  

### Conflict rule

If both a long and short setup could be argued on the same bar → **no trade** (fail closed). Bias must be unambiguous.

---

## Risk (still open — fill before live / size logic)

| Rule | Value | Status |
|------|--------|--------|
| Risk per trade | TBD % of equity | **open** |
| SL buffer (air) | TBD ticks/% under low (long) / over high (short) | **open** |
| Prefer R:R | **1:2 min**, prefer **1:3** | set |
| Max concurrent positions | TBD (BTC/ETH, long+short) | **open** |
| Max daily drawdown → stop day | TBD | **open** |
| Max leverage | TBD | **open** |
| Side | **Long hooks + short hooks** | set |
| Flat by session end | Yes (intraday) — TZ TBD | open |
| Same-symbol hedge (long+short BTC) | Default **no** — one position per symbol | open |

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

1. **Market data** — OHLCV 15m / 1h / 4h for BTC & ETH  
2. **Trend filter** — HH/HL (long bias) vs LH/LL (short bias) on 1h/4h  
3. **Hook detector**  
   - Long: after local HH → 1–3 red → hook = last red  
   - Short: after local LL → 1–3 green → hook = last green  
4. **Signal**  
   - Long: entry @ close, SL = hook.low − buffer, TP = entry + k×R  
   - Short: entry @ close, SL = hook.high + buffer, TP = entry − k×R  
5. **Risk gate** — size from risk%; block if daily DD / max positions  
6. **Paper broker** — market/limit fills; log trades  
7. **Exits** — TP, partial S/R, trail, or structure break (hook low/high)  

**Tests (minimum):**

| Case | Expect |
|------|--------|
| Valid long hook | signal long |
| Valid short hook | signal short |
| 4 red / 4 green pullback | reject |
| Long in downtrend / short in uptrend | reject |
| Entry mid-bar (not closed) | reject |
| Ambiguous dual setup | reject |

---

## Open questions for human

1. Exchange (Binance / Bybit / …) and contract (USDT-M perp)?  
2. Risk % per trade and max leverage?  
3. Exact SL buffer (ticks or %)?  
4. Session timezone / “flat by when”?  
5. Must **all** of 15m+1h+4h agree, or is 15m enough if 1h aligned?  
6. Max one position per symbol — confirm?  

---

## Changelog

| Date | Change |
|------|--------|
| 2026-07-13 | Assets BTC/ETH futures intraday; pattern **крючки** long rules locked |
| 2026-07-13 | **Short hooks** mirrored and locked (green 1–3 pullback, SL above high) |
