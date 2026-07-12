"""
Hook (крючки) detector — rules from docs/trading-brief.md.

Long:  uptrend + new high + 1–3 red pullback → long on last red close
Short: downtrend + new low + 1–3 green pullback → short on last green close
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

Side = Literal["long", "short"]


@dataclass(frozen=True)
class HookSignal:
    side: Side
    index: int  # entry bar index on entry TF (closed bar)
    time: pd.Timestamp
    entry: float
    stop: float
    hook_high: float
    hook_low: float
    pullback_len: int
    risk_per_unit: float  # abs(entry - stop) before buffer is already in stop

    @property
    def r_distance(self) -> float:
        return abs(self.entry - self.stop)


def is_red(row: pd.Series) -> bool:
    return float(row["close"]) < float(row["open"])


def is_green(row: pd.Series) -> bool:
    return float(row["close"]) > float(row["open"])


def higher_tf_bias(
    df_htf: pd.DataFrame,
    *,
    asof: pd.Timestamp,
    sma_len: int = 20,
) -> Literal["up", "down", "flat"]:
    """
    Simple bias: SMA slope + close vs SMA on higher TF (only bars fully closed asof).
    Not the full HH/HL structure engine — good enough for v0 paper tests.
    """
    if df_htf.empty:
        return "flat"
    sub = df_htf[df_htf["close_time"] <= asof]
    if len(sub) < sma_len + 2:
        return "flat"
    close = sub["close"].astype(float)
    sma = close.rolling(sma_len).mean()
    c0, c1 = float(close.iloc[-1]), float(close.iloc[-2])
    s0, s1 = float(sma.iloc[-1]), float(sma.iloc[-2])
    if np.isnan(s0) or np.isnan(s1):
        return "flat"
    if c0 > s0 and s0 >= s1:
        return "up"
    if c0 < s0 and s0 <= s1:
        return "down"
    return "flat"


def _pullback_red_len(df: pd.DataFrame, i: int) -> int:
    """How many consecutive red candles ending at i (inclusive)."""
    n = 0
    j = i
    while j >= 0 and is_red(df.iloc[j]):
        n += 1
        j -= 1
    return n


def _pullback_green_len(df: pd.DataFrame, i: int) -> int:
    n = 0
    j = i
    while j >= 0 and is_green(df.iloc[j]):
        n += 1
        j -= 1
    return n


def _had_new_high_before_pullback(df: pd.DataFrame, pullback_start: int, lookback: int = 30) -> bool:
    """Impulse: high just before pullback is local max in lookback window."""
    if pullback_start <= 0:
        return False
    end = pullback_start  # exclusive — last impulse bar index = pullback_start - 1
    start = max(0, end - lookback)
    window = df.iloc[start:end]
    if window.empty:
        return False
    impulse_high = float(df.iloc[end - 1]["high"])
    return impulse_high >= float(window["high"].max()) - 1e-12


def _had_new_low_before_pullback(df: pd.DataFrame, pullback_start: int, lookback: int = 30) -> bool:
    if pullback_start <= 0:
        return False
    end = pullback_start
    start = max(0, end - lookback)
    window = df.iloc[start:end]
    if window.empty:
        return False
    impulse_low = float(df.iloc[end - 1]["low"])
    return impulse_low <= float(window["low"].min()) + 1e-12


def detect_long_hook_at(
    df: pd.DataFrame,
    i: int,
    *,
    stop_buffer_pct: float = 0.0,
    min_pb: int = 1,
    max_pb: int = 3,
) -> HookSignal | None:
    if i < 2 or i >= len(df):
        return None
    row = df.iloc[i]
    if not is_red(row):
        return None
    pb = _pullback_red_len(df, i)
    if pb < min_pb or pb > max_pb:
        return None
    pullback_start = i - pb + 1
    # bar before pullback should be non-red impulse (prefer green / up bar)
    prev = df.iloc[pullback_start - 1]
    if is_red(prev):
        return None
    if not _had_new_high_before_pullback(df, pullback_start):
        return None

    entry = float(row["close"])
    hook_low = float(row["low"])
    hook_high = float(row["high"])
    stop = hook_low * (1.0 - stop_buffer_pct)
    if stop >= entry:
        return None
    return HookSignal(
        side="long",
        index=i,
        time=row["close_time"],
        entry=entry,
        stop=stop,
        hook_high=hook_high,
        hook_low=hook_low,
        pullback_len=pb,
        risk_per_unit=entry - stop,
    )


def detect_short_hook_at(
    df: pd.DataFrame,
    i: int,
    *,
    stop_buffer_pct: float = 0.0,
    min_pb: int = 1,
    max_pb: int = 3,
) -> HookSignal | None:
    if i < 2 or i >= len(df):
        return None
    row = df.iloc[i]
    if not is_green(row):
        return None
    pb = _pullback_green_len(df, i)
    if pb < min_pb or pb > max_pb:
        return None
    pullback_start = i - pb + 1
    prev = df.iloc[pullback_start - 1]
    if is_green(prev):
        return None
    if not _had_new_low_before_pullback(df, pullback_start):
        return None

    entry = float(row["close"])
    hook_low = float(row["low"])
    hook_high = float(row["high"])
    stop = hook_high * (1.0 + stop_buffer_pct)
    if stop <= entry:
        return None
    return HookSignal(
        side="short",
        index=i,
        time=row["close_time"],
        entry=entry,
        stop=stop,
        hook_high=hook_high,
        hook_low=hook_low,
        pullback_len=pb,
        risk_per_unit=stop - entry,
    )


def scan_hooks(
    df_15m: pd.DataFrame,
    df_1h: pd.DataFrame | None = None,
    df_4h: pd.DataFrame | None = None,
    *,
    stop_buffer_pct: float = 0.0005,
    require_htf_bias: bool = True,
) -> list[HookSignal]:
    """
    Scan closed 15m bars for long/short hooks.
    If require_htf_bias: long only when 1h or 4h bias up; short only when down.
    """
    signals: list[HookSignal] = []
    for i in range(len(df_15m)):
        asof = df_15m.iloc[i]["close_time"]
        bias_1h = higher_tf_bias(df_1h, asof=asof) if df_1h is not None else "flat"
        bias_4h = higher_tf_bias(df_4h, asof=asof) if df_4h is not None else "flat"

        long_ok = True
        short_ok = True
        if require_htf_bias:
            # allow if either HTF agrees and neither is opposite
            long_ok = (bias_1h == "up" or bias_4h == "up") and bias_1h != "down" and bias_4h != "down"
            short_ok = (bias_1h == "down" or bias_4h == "down") and bias_1h != "up" and bias_4h != "up"
            # if no HTF data, fall back to entry-TF only
            if df_1h is None and df_4h is None:
                long_ok = short_ok = True

        long_sig = detect_long_hook_at(df_15m, i, stop_buffer_pct=stop_buffer_pct) if long_ok else None
        short_sig = detect_short_hook_at(df_15m, i, stop_buffer_pct=stop_buffer_pct) if short_ok else None

        # fail closed on dual setup
        if long_sig and short_sig:
            continue
        if long_sig:
            signals.append(long_sig)
        if short_sig:
            signals.append(short_sig)
    return signals
