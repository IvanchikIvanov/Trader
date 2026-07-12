"""Interactive backtest chart — entries, exits, SL/TP, equity (Plotly HTML)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from trader.backtest import BacktestResult, Trade


def plot_backtest(
    df_15m: pd.DataFrame,
    result: BacktestResult,
    *,
    symbol: str = "BTCUSDT",
    title: str | None = None,
    max_bars: int | None = None,
) -> "go.Figure":
    """
    Build a Plotly figure:
    - candlesticks (15m)
    - long/short entry markers
    - exit markers (TP/SL/eod/timeout)
    - entry→exit connectors + SL/TP dashed levels per trade
    - equity curve subplot
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    df = df_15m.copy()
    if max_bars is not None and len(df) > max_bars:
        df = df.iloc[-max_bars:].reset_index(drop=True)
        t_min = df["open_time"].iloc[0]
        trades = [
            t
            for t in result.trades
            if t.exit_time is not None and t.exit_time >= t_min
            or (t.entry_time is not None and t.entry_time >= t_min)
        ]
    else:
        trades = list(result.trades)

    s = result.summary()
    fig_title = title or (
        f"{symbol} hooks paper · trades={s['trades']} win={s['win_rate']:.0%} "
        f"avgR={s['avg_r']} ret={s['return_pct']}%"
    )

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.72, 0.28],
        subplot_titles=(fig_title, "Paper equity"),
    )

    # Candles
    fig.add_trace(
        go.Candlestick(
            x=df["open_time"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="15m",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
            showlegend=True,
        ),
        row=1,
        col=1,
    )

    long_e_t, long_e_p, long_e_txt = [], [], []
    short_e_t, short_e_p, short_e_txt = [], [], []
    exit_t, exit_p, exit_txt, exit_color = [], [], [], []

    for i, t in enumerate(trades):
        stop_s = f"{t.stop:.2f}" if t.stop is not None else "off"
        tp_s = f"{t.tp:.2f}" if t.tp is not None else "off"
        hover = (
            f"#{i+1} {t.side.upper()}<br>"
            f"entry={t.entry:.2f} stop={stop_s} tp={tp_s}<br>"
            f"exit={t.exit} ({t.exit_reason})<br>"
            f"pnl={t.pnl:+.2f} R={t.r_multiple:+.2f}"
            + (f"<br>stake={t.stake:.0f} lev={t.leverage:.0f}x" if t.stake else "")
        )
        if t.side == "long":
            long_e_t.append(t.entry_time)
            long_e_p.append(t.entry)
            long_e_txt.append(hover)
        else:
            short_e_t.append(t.entry_time)
            short_e_p.append(t.entry)
            short_e_txt.append(hover)

        if t.exit_time is not None and t.exit is not None:
            exit_t.append(t.exit_time)
            exit_p.append(t.exit)
            exit_txt.append(hover)
            exit_color.append("#26a69a" if t.pnl >= 0 else "#ef5350")

            # connector entry → exit
            fig.add_trace(
                go.Scatter(
                    x=[t.entry_time, t.exit_time],
                    y=[t.entry, t.exit],
                    mode="lines",
                    line=dict(
                        color="rgba(100,181,246,0.55)" if t.side == "long" else "rgba(255,167,38,0.55)",
                        width=1.5,
                        dash="dot",
                    ),
                    hoverinfo="skip",
                    showlegend=False,
                ),
                row=1,
                col=1,
            )
            # SL / TP horizontal during trade (if enabled)
            if t.stop is not None:
                fig.add_trace(
                    go.Scatter(
                        x=[t.entry_time, t.exit_time],
                        y=[t.stop, t.stop],
                        mode="lines",
                        line=dict(color="rgba(239,83,80,0.45)", width=1, dash="dash"),
                        hoverinfo="skip",
                        showlegend=False,
                    ),
                    row=1,
                    col=1,
                )
            if t.tp is not None:
                fig.add_trace(
                    go.Scatter(
                        x=[t.entry_time, t.exit_time],
                        y=[t.tp, t.tp],
                        mode="lines",
                        line=dict(color="rgba(38,166,154,0.45)", width=1, dash="dash"),
                        hoverinfo="skip",
                        showlegend=False,
                    ),
                    row=1,
                    col=1,
                )

    if long_e_t:
        fig.add_trace(
            go.Scatter(
                x=long_e_t,
                y=long_e_p,
                mode="markers",
                name="Long entry",
                marker=dict(symbol="triangle-up", size=11, color="#00e676", line=dict(width=1, color="#000")),
                text=long_e_txt,
                hoverinfo="text",
            ),
            row=1,
            col=1,
        )
    if short_e_t:
        fig.add_trace(
            go.Scatter(
                x=short_e_t,
                y=short_e_p,
                mode="markers",
                name="Short entry",
                marker=dict(symbol="triangle-down", size=11, color="#ff1744", line=dict(width=1, color="#000")),
                text=short_e_txt,
                hoverinfo="text",
            ),
            row=1,
            col=1,
        )
    if exit_t:
        fig.add_trace(
            go.Scatter(
                x=exit_t,
                y=exit_p,
                mode="markers",
                name="Exit",
                marker=dict(
                    symbol="x",
                    size=9,
                    color=exit_color,
                    line=dict(width=1.5, color="#333"),
                ),
                text=exit_txt,
                hoverinfo="text",
            ),
            row=1,
            col=1,
        )

    # Equity
    if result.equity_curve:
        eq_t = [x[0] for x in result.equity_curve]
        eq_v = [x[1] for x in result.equity_curve]
        if max_bars is not None and len(df) > 0:
            t0 = df["open_time"].iloc[0]
            pairs = [(a, b) for a, b in zip(eq_t, eq_v) if a >= t0]
            if pairs:
                eq_t, eq_v = zip(*pairs)
                eq_t, eq_v = list(eq_t), list(eq_v)
        fig.add_trace(
            go.Scatter(
                x=eq_t,
                y=eq_v,
                mode="lines",
                name="Equity",
                line=dict(color="#7c4dff", width=2),
                fill="tozeroy",
                fillcolor="rgba(124,77,255,0.12)",
            ),
            row=2,
            col=1,
        )
        fig.add_hline(
            y=result.starting_equity,
            line_dash="dot",
            line_color="gray",
            row=2,
            col=1,
            annotation_text="start",
        )

    fig.update_layout(
        template="plotly_dark",
        height=900,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=50, r=20, t=60, b=40),
        hovermode="x unified",
    )
    fig.update_xaxes(title_text="Time (UTC)", row=2, col=1)
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Equity $", row=2, col=1)
    # rangeslider only on price for zoom/pan
    fig.update_xaxes(rangeslider_visible=True, row=1, col=1)
    fig.update_xaxes(rangeslider_thickness=0.05, row=1, col=1)

    return fig


def save_chart(
    df_15m: pd.DataFrame,
    result: BacktestResult,
    path: Path,
    *,
    symbol: str = "BTCUSDT",
    max_bars: int | None = None,
    open_browser: bool = False,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig = plot_backtest(df_15m, result, symbol=symbol, max_bars=max_bars)
    fig.write_html(str(path), include_plotlyjs="cdn", full_html=True)
    if open_browser:
        import webbrowser

        webbrowser.open(path.resolve().as_uri())
    return path
