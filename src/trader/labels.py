"""Compare human gold hooks vs detector."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from trader.data import fetch_klines
from trader.hooks import detect_long_hook_at, detect_short_hook_at


def load_gold_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, comment="#")
    df["time_utc"] = pd.to_datetime(df["time_utc"], utc=True)
    return df


def check_label_row(row: pd.Series, *, stop_buffer_pct: float = 0.0005) -> dict:
    symbol = str(row["symbol"]).upper()
    t: pd.Timestamp = row["time_utc"]
    side = str(row["side"]).lower()
    status = str(row.get("status", "gold")).lower()

    start = (t - timedelta(days=3)).to_pydatetime()
    end = (t + timedelta(days=1)).to_pydatetime()
    df = fetch_klines(symbol, "15m", start=start, end=end)
    match = df["open_time"] == t
    if not match.any():
        return {
            "symbol": symbol,
            "time_utc": str(t),
            "side": side,
            "status": status,
            "bar_found": False,
            "detected": False,
            "verdict": "NO_BAR",
            "note": row.get("note", ""),
        }
    i = int(df.index[match][0])
    bar = df.iloc[i]
    if side == "long":
        sig = detect_long_hook_at(df, i, stop_buffer_pct=stop_buffer_pct)
    else:
        sig = detect_short_hook_at(df, i, stop_buffer_pct=stop_buffer_pct)
    detected = sig is not None

    if status == "gold":
        verdict = "HIT" if detected else "MISS"
    elif status == "reject":
        verdict = "OK_REJECT" if not detected else "FALSE_POS"
    else:
        verdict = "UNKNOWN_STATUS"

    return {
        "symbol": symbol,
        "time_utc": str(t),
        "side": side,
        "status": status,
        "bar_found": True,
        "o": float(bar["open"]),
        "h": float(bar["high"]),
        "l": float(bar["low"]),
        "c": float(bar["close"]),
        "detected": detected,
        "verdict": verdict,
        "note": row.get("note", ""),
    }


def audit_labels(path: Path) -> list[dict]:
    gold = load_gold_csv(path)
    return [check_label_row(row) for _, row in gold.iterrows()]
