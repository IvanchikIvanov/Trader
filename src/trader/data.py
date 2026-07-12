"""Public OHLCV fetch — Binance USDT-M futures (no API key, no deposit)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

import pandas as pd
import requests

BINANCE_FAPI_KLINES = "https://fapi.binance.com/fapi/v1/klines"

INTERVAL_MS = {
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
}


def _ms(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def fetch_klines(
    symbol: str,
    interval: str,
    *,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 1500,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """
    Download OHLCV from Binance futures public API.

    symbol: e.g. BTCUSDT, ETHUSDT
    interval: 15m, 1h, 4h, ...
    """
    if interval not in INTERVAL_MS:
        raise ValueError(f"Unsupported interval {interval!r}")

    sess = session or requests.Session()
    rows: list[list] = []
    start_ms = _ms(start) if start else None
    end_ms = _ms(end) if end else None
    cursor = start_ms

    while True:
        params: dict = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": min(limit, 1500),
        }
        if cursor is not None:
            params["startTime"] = cursor
        if end_ms is not None:
            params["endTime"] = end_ms

        resp = sess.get(BINANCE_FAPI_KLINES, params=params, timeout=30)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break

        rows.extend(batch)
        last_open = batch[-1][0]
        next_cursor = last_open + INTERVAL_MS[interval]
        if end_ms is not None and next_cursor > end_ms:
            break
        if cursor is not None and next_cursor <= cursor:
            break
        if len(batch) < params["limit"]:
            break
        # no start: single page is enough for quick tests
        if start_ms is None:
            break
        cursor = next_cursor

    if not rows:
        return _empty_ohlcv()

    return klines_to_df(rows)


def klines_to_df(rows: Iterable[list]) -> pd.DataFrame:
    data = []
    for r in rows:
        data.append(
            {
                "open_time": pd.to_datetime(int(r[0]), unit="ms", utc=True),
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
                "volume": float(r[5]),
                "close_time": pd.to_datetime(int(r[6]), unit="ms", utc=True),
            }
        )
    df = pd.DataFrame(data).drop_duplicates(subset=["open_time"]).sort_values("open_time")
    df = df.reset_index(drop=True)
    return df


def _empty_ohlcv() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["open_time", "open", "high", "low", "close", "volume", "close_time"]
    )


def synthetic_trend_with_long_hook(n_up: int = 20) -> pd.DataFrame:
    """Deterministic 15m-like bars: uptrend + 2 red hook — for unit tests."""
    rows = []
    price = 100.0
    t0 = pd.Timestamp("2024-01-01", tz="UTC")
    # impulse up
    for i in range(n_up):
        o = price
        c = price + 1.0
        rows.append(_bar(t0 + pd.Timedelta(minutes=15 * i), o, c + 0.2, o - 0.1, c))
        price = c
    # new high then 2 red hook
    o = price
    c = price + 1.5
    rows.append(_bar(t0 + pd.Timedelta(minutes=15 * n_up), o, c + 0.1, o, c))  # HH green
    price = c
    # red 1
    o = price
    c = price - 0.8
    rows.append(_bar(t0 + pd.Timedelta(minutes=15 * (n_up + 1)), o, o + 0.1, c - 0.1, c))
    price = c
    # red 2 = hook
    o = price
    c = price - 0.5
    rows.append(_bar(t0 + pd.Timedelta(minutes=15 * (n_up + 2)), o, o + 0.05, c - 0.2, c))
    return pd.DataFrame(rows)


def synthetic_trend_with_short_hook(n_down: int = 20) -> pd.DataFrame:
    rows = []
    price = 200.0
    t0 = pd.Timestamp("2024-01-01", tz="UTC")
    for i in range(n_down):
        o = price
        c = price - 1.0
        rows.append(_bar(t0 + pd.Timedelta(minutes=15 * i), o, o + 0.1, c - 0.2, c))
        price = c
    o = price
    c = price - 1.5
    rows.append(_bar(t0 + pd.Timedelta(minutes=15 * n_down), o, o + 0.05, c - 0.1, c))  # LL red
    price = c
    # green 1
    o = price
    c = price + 0.8
    rows.append(_bar(t0 + pd.Timedelta(minutes=15 * (n_down + 1)), o, c + 0.1, o - 0.05, c))
    price = c
    # green 2 = hook
    o = price
    c = price + 0.5
    rows.append(_bar(t0 + pd.Timedelta(minutes=15 * (n_down + 2)), o, c + 0.2, o - 0.05, c))
    return pd.DataFrame(rows)


def _bar(open_time, o, h, l, c, vol=1.0):
    return {
        "open_time": open_time,
        "open": float(o),
        "high": float(h),
        "low": float(l),
        "close": float(c),
        "volume": float(vol),
        "close_time": open_time + pd.Timedelta(minutes=15) - pd.Timedelta(milliseconds=1),
    }
