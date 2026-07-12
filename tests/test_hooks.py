"""Unit tests for крючки detector — no network."""

from trader.data import synthetic_trend_with_long_hook, synthetic_trend_with_short_hook
from trader.hooks import detect_long_hook_at, detect_short_hook_at, scan_hooks
from trader.backtest import BacktestConfig, run_backtest


def test_long_hook_detected_on_synthetic():
    df = synthetic_trend_with_long_hook()
    # last bar should be the hook
    i = len(df) - 1
    sig = detect_long_hook_at(df, i, stop_buffer_pct=0.0)
    assert sig is not None
    assert sig.side == "long"
    assert sig.entry == float(df.iloc[i]["close"])
    assert sig.stop <= float(df.iloc[i]["low"]) + 1e-9


def test_short_hook_detected_on_synthetic():
    df = synthetic_trend_with_short_hook()
    i = len(df) - 1
    sig = detect_short_hook_at(df, i, stop_buffer_pct=0.0)
    assert sig is not None
    assert sig.side == "short"
    assert sig.stop >= float(df.iloc[i]["high"]) - 1e-9


def test_four_red_rejected():
    df = synthetic_trend_with_long_hook()
    # append extra reds so pullback > 3
    import pandas as pd

    last = df.iloc[-1]
    price = float(last["close"])
    extra = []
    for k in range(3):
        o = price
        c = price - 0.3
        t = last["open_time"] + pd.Timedelta(minutes=15 * (k + 1))
        extra.append(
            {
                "open_time": t,
                "open": o,
                "high": o,
                "low": c - 0.1,
                "close": c,
                "volume": 1.0,
                "close_time": t + pd.Timedelta(minutes=15) - pd.Timedelta(milliseconds=1),
            }
        )
        price = c
    df2 = pd.concat([df, pd.DataFrame(extra)], ignore_index=True)
    sig = detect_long_hook_at(df2, len(df2) - 1)
    assert sig is None  # 2 original red + 3 = 5 reds


def test_scan_and_backtest_runs():
    df = synthetic_trend_with_long_hook(n_up=25)
    # pad with more bars so exit can resolve
    import pandas as pd

    last = df.iloc[-1]
    price = float(last["close"])
    rows = []
    for k in range(20):
        o = price
        # continue up → hit TP for long
        c = price + 0.8
        t = last["open_time"] + pd.Timedelta(minutes=15 * (k + 1))
        rows.append(
            {
                "open_time": t,
                "open": o,
                "high": c + 0.2,
                "low": o - 0.1,
                "close": c,
                "volume": 1.0,
                "close_time": t + pd.Timedelta(minutes=15) - pd.Timedelta(milliseconds=1),
            }
        )
        price = c
    df2 = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    sigs = scan_hooks(df2, require_htf_bias=False)
    assert any(s.side == "long" for s in sigs)
    result = run_backtest(df2, config=BacktestConfig(require_htf_bias=False, rr_target=2.0))
    assert result.n_trades >= 1
