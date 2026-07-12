"""Chart builds without network."""

from pathlib import Path

import pandas as pd

from trader.backtest import BacktestConfig, run_backtest
from trader.chart import plot_backtest, save_chart
from trader.data import synthetic_trend_with_long_hook


def _df_with_followthrough():
    df = synthetic_trend_with_long_hook(n_up=25)
    last = df.iloc[-1]
    price = float(last["close"])
    rows = []
    for k in range(20):
        o = price
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
    return pd.concat([df, pd.DataFrame(rows)], ignore_index=True)


def test_plot_backtest_builds_payload():
    df = _df_with_followthrough()
    result = run_backtest(df, config=BacktestConfig(require_htf_bias=False))
    payload = plot_backtest(df, result, symbol="TEST")
    assert payload is not None
    assert "candles" in payload
    assert len(payload["candles"]) >= 2
    assert "markers" in payload


def test_save_chart_html_tv(tmp_path: Path):
    df = _df_with_followthrough()
    result = run_backtest(df, config=BacktestConfig(require_htf_bias=False))
    out = tmp_path / "t.html"
    save_chart(df, result, out, symbol="TEST")
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "lightweight-charts" in text.lower()
    assert "Europe/Moscow" in text or "Москва" in text
