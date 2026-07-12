# Case: HYPEUSDT 4H long-hook (gold structure for AI agents)

> Detailed chart description for agent training / detector tuning.  
> Venue in description: **Bybit** HYPEUSDT perpetual. Paper only unless human enables live.

| Field | Value |
|-------|--------|
| Symbol | **HYPEUSDT** perpetual |
| Venue (source) | **Bybit** (Binance may differ slightly) |
| TF (entry / hook) | **4H** |
| Side | **Long** |
| Screenshot time | ~**2026-07-16 08:45 UTC** |
| Price at description | **69.546** (+4.02%) |
| Visible range | ~63.35 – ~71.50 |
| Role | Clear **post-hoc** long hook with follow-through |

---

## Agent summary (one paragraph)

On HYPEUSDT 4H, after a strong green impulse that updated the high (~open 65.40 → close ~68.20–68.40), a **red pullback candle** formed (open ~68.20–68.40, high ~68.50–68.60, low ~66.80–67.00, close ~67.10–67.30). That red candle is the **long hook**. Strategy entry is on **close of that red candle**. After the hook, a large green continuation bar (~67.1 → ~69.5–69.8) broke the prior high — textbook trend continuation after the hook.

---

## Candle sequence (left → right)

Approximate OHLC from human chart read (Bybit 4H). Use as structure, not exact exchange ticks until pinned to API.

### 1. Large green (around 15 Jul)

| | approx |
|--|--------|
| Open | 63.70–63.90 |
| Close | 65.40–65.60 |
| Note | Long body, strong impulse up |

### 2. Green continuation

| | approx |
|--|--------|
| Open | ~65.40 |
| Close | 66.50–66.70 |
| Note | Continuation of advance |

### 3. Red (first pullback — *not* the marked hook)

| | approx |
|--|--------|
| Open | 66.50–66.70 |
| Close | 65.30–65.50 |
| Note | Small body, wicks both sides — earlier pullback |

### 4. Large green — **impulse before hook**

| | approx |
|--|--------|
| Open | ~65.40 |
| Close | 68.20–68.40 |
| Note | Strong rally, **new high** — required before long hook |

### 5. Red — **THE HOOK** (red arrow V on chart)

| | approx |
|--|--------|
| Open | 68.20–68.40 |
| High | 68.50–68.60 |
| Low | 66.80–67.00 |
| Close | 67.10–67.30 |
| Color | Red body, modest size, lower wick |
| **Label** | **Long hook** |

**Strategy mapping**

| Rule | Application |
|------|-------------|
| Impulse | Candle #4 green to ~68.4 |
| Hook | Candle #5 red |
| Entry | **Market/limit at close ~67.1–67.3** (when #5 closed) |
| Stop | Under hook low ~**66.8–67.0** (− optional air) |
| Invalidation | Break below hook low after entry |
| Follow-through | Candle #6 green proves continuation (for review, not required at entry) |

### 6. Large green after hook (follow-through)

| | approx |
|--|--------|
| Open | 67.10–67.30 |
| Close | 69.50–69.80 |
| Note | Long bullish body, breaks prior high — strong continuation |

---

## Current situation (right side of screenshot)

- Price ~**69.546**
- Last visible bar: large green
- High updated **after** the hook
- Two MAs visible (cyan + orange) — optional context, **not** required for hook definition

---

## Why this is a clean gold example for the AI

1. **Clear impulse** to a new high before the red.  
2. **Single identifiable red hook** (not a 5-bar mess).  
3. Entry defined **only at red close** — no mid-bar fantasy.  
4. **Follow-through** green validates the pattern historically (good for teaching; live you don’t wait for #6 to enter).  
5. TF is **4H** — same pattern language as 15m/1H: impulse → opposite color pullback → enter on close.

---

## Formal checklist (long, this chart)

```
[x] Higher-TF / sequence bias: up (greens, HH)
[x] Recent impulse bar: large green to ~68.4
[x] Pullback: red candle after impulse
[x] Hook = that red candle (closed ~67.1–67.3)
[x] Entry long at hook close
[x] SL under hook low (~66.8–67.0)
[ ] TP: min 1:2–1:3 vs stop OR structure targets (user-defined)
[x] Post-entry: continuation green (for post-trade review only)
```

---

## Anti-confusion for the agent

| Do | Don't |
|----|--------|
| Treat **candle #5** as the hook | Treat candle #3 (earlier red) as the marked hook |
| Enter on **close** of #5 | Enter mid-#5 or on #6 open only as “late” |
| Measure SL from **#5 low** | Put SL under #3 or under 63s |
| Use Bybit OHLC if trading Bybit | Assume Binance OHLC identical without check |

---

## Link to project rules

- Pattern language: `docs/trading-brief.md` (impulse → red hook → close entry).  
- Deep vs shallow: this hook is a moderate pullback into ~67 from ~68.5 high — still one red after impulse.  
- Bot v0 scans BTC/ETH 15m; this case teaches **4H multi-asset** hooks until HYPE is added to the scanner.

---

## Pin to exchange timestamp (TODO)

When API OHLC is matched:

| Field | Value |
|-------|--------|
| `time_utc` (4H open) | TBD |
| `user_said` | HYPE 4H long hook ~16 Jul 2026 chart |
| Gold CSV row | optional once open time locked |

Search window: 4H bars with open ~68.2–68.4, low ~66.8–67.0, close ~67.1–67.3 after a green bar closing ~68.2–68.4.
