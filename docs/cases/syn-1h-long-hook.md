# Case: SYN 1H long-hook (user analysis)

> Snapshot of how **you** read a live/forming hook.  
> Not auto-traded. Paper / human only until risk + universe locked.

| Field | Value |
|-------|--------|
| Symbol | **SYN** (spot/perp — confirm venue) |
| TF (entry) | **1H** |
| Side | **Long** |
| Status | Forming / wait for **candle close** |
| Time context | ~6h to close (possibly weekly close on that bar) |
| Captured | from user description |

---

## What you see (structure)

1. **Impulse up** — large **green** candle = update of the high (new high / impulse bar).  
2. **Pullback down** — **red** candle forming = the **long hook**.  
3. Hook is defined on **this red candle**, not mid-bar entries.  
4. Price tagged ~**0.26** zone (your white mark); bounce off red low (~0.30758 mentioned as interim bounce).

```
  [ big green impulse / new high ]
           \
            \  red pullback  ← LONG HOOK candle
             \
          low ~0.26 zone
```

---

## Pros (your read)

- Clear impulse before the hook (big green).  
- Pullback already deep into ~0.26 zone.  
- If red **closes** near current levels or slightly lower → classic **long hook by your rule** (enter on close).

## Cons / risks (your read)

- Pullback **deep** (~30–40% of impulse). Classic “Ross-style” often treats deep hooks as weak; **your version** still allows entry **on close**.  
- Price already bounced off the red low — close may improve or invalidate.

---

## Plan by your rules

| Step | Rule |
|------|------|
| **Entry** | On **close** of this red 1H candle (~6h). Prefer red close or long lower wick still as pullback close. |
| **Stop** | Under red low (~0.26 mark); optional air **0.255–0.258** |
| **TP** | Min **0.40**; scale optional **0.38–0.39** then hold rest to 0.40+ |
| **R:R** | Stop ~0.26 → TP 0.40 ≈ **1:3+** if levels hold |

**Do not enter before close** — same discipline as BTC 15m hooks.

---

## Mapping to engine (how the bot thinks)

| Your SYN 1H language | Code / brief concept |
|----------------------|----------------------|
| Big green before | Impulse / new high bar |
| Red candle = hook | Long hook candle (`is_red`, pullback 1–3) |
| Enter on red close | `entry = close` of hook bar |
| SL under red low | `stop = hook.low − buffer` |
| TP 0.40 / partials | Fixed levels *or* R-multiple (1:2–1:3) |

Bot today is wired for **BTC/ETH 15m** paper. Same **logic** can run on **SYN 1H** if we add the symbol to universe + TF=1h.

---

## Checklist before this trade (human)

- [ ] Red 1H **closed** (not “almost”)  
- [ ] Still accept deep pullback (your version)  
- [ ] SL placed under low + air  
- [ ] Size from risk % (not from “want 0.40”)  
- [ ] Paper or tiny size only until live gate  

---

## Open questions

1. SYN **spot** or **USDT-M futures**?  
2. Add SYN permanently to tradable universe alongside BTC/ETH?  
3. On alts: primary TF **1H** (and weekly context) vs 15m on BTC?  
