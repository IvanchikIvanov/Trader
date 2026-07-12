---
name: hook-from-screenshot
description: >
  When the user drops a chart screenshot of a found крючок (hook), read the image,
  extract symbol/TF/side/time, save via trader hook tool into gold labels.
  Use whenever user sends a chart image, TradingView/Bybit/Binance screenshot,
  or says "крючок на скрине" / "разбери скрин".
user_invocable: true
---

# Hook from screenshot

User sends **images**, not text rows. You must **look at the image**.

## Steps

1. **Save the shot into the repo inbox** if you only received an attachment path — copy or instruct:
   ```bash
   # If file is already on disk:
   python -m trader hook shot "PATH/TO/image.png"
   ```
   Or user dropped into `labels/inbox/`:
   ```bash
   python -m trader hook ingest
   ```

2. **Read the image** with the image/read tool. Extract:
   - Symbol (BTCUSDT, ETH, SYN, HYPE, …)
   - Timeframe (15m / 1h / 4h / 1D)
   - Side: long (red hook after green impulse) or short (green hook after red impulse)
   - **Open time of the hook candle** in chart timezone — user uses **MSK** by default
   - Any arrows/marks the user drew

3. **Confirm briefly** if ambiguous (timezone, which of two arrows).

4. **Write gold label**:
   ```bash
   python -m trader hook label <CARD_ID> --symbol BTCUSDT --tf 15m --side long --when "2026-07-12 05:00" --note "from screenshot"
   ```
   Or edit `labels/hooks_gold.csv` + mark card labeled.

5. **Do not** invent strategy rules. **Do not** live trade. Paper/labels only unless asked.

## Output to user

- What you saw (1–2 lines)
- Parsed fields (symbol, TF, side, MSK time)
- Card id + path under `labels/screenshots/`
- That it's in gold set (or pending if time unclear)

## If time not readable on screenshot

Save as pending card, ask user: «какое open MSK у свечи-крюка?»
