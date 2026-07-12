# Case: SYN 1D — two long hooks after impulse (AI agent brief)

> Second SYN screenshot: **daily** chart, **two** consecutive long hooks.  
> Paper / human only. Do not auto-trade.

| Field | Value |
|-------|--------|
| Symbol | **SYN / USDT** (spot or perp — confirm venue) |
| TF (entry / hook) | **1D (Daily)** |
| Side | **Long** (both hooks) |
| Price at description | **0.47488** (−15.74% day context) |
| Day OHLC (current bar context) | O **0.56321** · H **0.58295** · L **0.45063** · prior close **0.47488** |
| User intent | **Do not miss close** of the current red (2nd hook) → long per strategy |

---

## Agent summary (one paragraph)

On SYN **daily**, after a strong green impulse that updated highs, **two long hooks** appear in sequence. **Hook 1** (lower red arrow, **missed by user**): small red after impulse with a **long lower wick** (stops underneath — user notes nearly ideal form). **Hook 2** (upper red arrow, **current**): deeper red pullback after further strength — open ~0.52–0.53, high ~0.58–0.585, low ~0.46–0.47, close ~0.474–0.480 (still forming / watch close). User plans to enter long **on close of this second red**, not mid-bar. Price still trading near **0.47488** after the second hook structure.

---

## Structure (left → right)

### Background

- Strong **up** impulse: green dailies, higher highs.
- Bias for long hooks: **up only**.

### Hook 1 — lower red arrow (**missed**)

| | |
|--|--|
| Type | Small **red** after impulse |
| Feature | **Long lower wick** |
| User note | Stops sat under the wick; “almost ideal” formation |
| Status | **Skipped live** — gold as *retrospective* quality example + lesson (don’t miss close) |
| SL teaching | Under wick low (air optional) |

```
  greens / HH
       \
        red + long lower wick  ← HOOK 1 (missed)
         |
        wick low = stop zone
```

### Hook 2 — upper red arrow (**current / primary plan**)

| | approx |
|--|--------|
| Open | 0.520–0.530 |
| High | 0.580–0.585 |
| Low | 0.460–0.470 |
| Close | 0.474–0.480 (watch final daily close) |
| Character | Red body, **deeper** pullback from prior high |
| Status | **Active** — user waits for **daily close** then long |

**Strategy mapping (hook 2)**

| Rule | Application |
|------|-------------|
| Impulse | Prior green / HH sequence into the red |
| Hook | This red daily |
| Entry | **On close** of red (~0.474–0.48 if it holds as red/pullback close) |
| Stop | Under hook low ~**0.46–0.47** (− optional air; day low shown **0.45063** may be same bar) |
| Invalidation | Break below hook low after entry |
| Depth | Deeper than hook 1 — still valid under **user’s** “enter on close” version |

```
  strong up / new highs
           \
            red deep pullback  ← HOOK 2 (current)
             low ~0.46–0.47
              close ~0.47–0.48 → ENTER LONG ON CLOSE
```

---

## Day stats vs hook 2 (consistency check for agent)

| Field | Value | Agent note |
|-------|--------|------------|
| Open | 0.56321 | Fits “opened higher, sold off red” |
| High | 0.58295 | Fits high ~0.58–0.585 |
| Low | 0.45063 | Slightly **below** ~0.46–0.47 band — prefer **actual bar low** for SL |
| Last / close ref | 0.47488 | Near described close zone |

**Use exchange OHLC for final SL**, not only approx text.

---

## Two-hook sequence — rules for the agent

| Priority | Action |
|----------|--------|
| 1 | Prefer **hook that is closing now** (hook 2) for live plan |
| 2 | Hook 1 = **missed opportunity** / training; do not invent a late entry on hook 1 mid-structure |
| 3 | **One position logic**: default one long from hook 2 close; don’t stack two hooks without human rule |
| 4 | Deeper hook 2 ≠ automatic reject (user version allows deep daily pullbacks if close entry) |
| 5 | **Never enter before daily close** of the hook candle |

---

## Formal checklist (long, hook 2)

```
[x] Bias: uptrend / HH before the reds
[x] Hook 1 existed (small red + long lower wick) — missed, retrospective gold quality
[x] Hook 2: red daily after strength (deeper)
[ ] Wait for HOOK 2 daily CLOSE (user plan)
[ ] Entry long at that close
[ ] SL under true bar low (≤ ~0.45063 area / hook low)
[ ] TP: min 1:2–1:3 or structure (user TBD)
[ ] Paper or human size only
```

---

## Anti-confusion

| Do | Don't |
|----|--------|
| Treat **upper arrow** as active setup | Re-enter “hook 1” after it’s long gone without a new close rule |
| Enter on **1D close** of hook 2 | Scalp mid-day on 1D chart as if close already happened |
| SL under **actual low** of hook 2 | SL only at 0.46 if print was 0.45063 |
| Compare to SYN 1H case as same language | Assume 1H and 1D hook are the same bar |

---

## Related docs

- Pattern language: `docs/trading-brief.md`  
- SYN 1H forming hook: `docs/cases/syn-1h-long-hook.md`  
- HYPE 4H clean hook: `docs/cases/hypeusdt-4h-long-hook.md`  

---

## Open questions

1. Exact **daily open_time** (UTC) for hook 1 and hook 2 once date pinned.  
2. Spot vs futures for SYN.  
3. After hook 2 entry: target levels (e.g. back to 0.58 / extension) vs pure R-multiple.  
4. If hook 2 closes **green** (recovery day) — setup cancelled or still a hook? Default: **fail closed** unless user redefines.  
