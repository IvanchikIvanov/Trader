"""
TradingView-style backtest chart (Lightweight Charts).

Looks/zooms like TradingView: candles, crosshair, scroll/pinch zoom,
entry/exit markers, optional equity pane. Times labeled in Europe/Moscow.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from trader.backtest import BacktestResult, Trade


def _to_unix(ts: pd.Timestamp) -> int:
    t = pd.Timestamp(ts)
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    else:
        t = t.tz_convert("UTC")
    return int(t.timestamp())


def _prepare_frame(
    df_15m: pd.DataFrame,
    result: BacktestResult,
    max_bars: int | None,
) -> tuple[pd.DataFrame, list[Trade]]:
    df = df_15m.copy().reset_index(drop=True)
    if max_bars is not None and len(df) > max_bars:
        df = df.iloc[-max_bars:].reset_index(drop=True)
        t_min = df["open_time"].iloc[0]
        trades = [
            t
            for t in result.trades
            if (t.exit_time is not None and t.exit_time >= t_min)
            or (t.entry_time is not None and t.entry_time >= t_min)
        ]
    else:
        trades = list(result.trades)
    return df, trades


def _nearest_bar_time(df: pd.DataFrame, ts: pd.Timestamp) -> int | None:
    """Map any timestamp to candle open_time unix (required by lightweight-charts markers)."""
    if df.empty:
        return None
    target = pd.Timestamp(ts)
    if target.tzinfo is None:
        target = target.tz_localize("UTC")
    # prefer bar whose close_time matches entry (our signals use close)
    closes = pd.to_datetime(df["close_time"], utc=True)
    exact = df.index[closes == target]
    if len(exact):
        return _to_unix(df.loc[exact[0], "open_time"])
    # fallback: last bar with open_time <= ts
    opens = pd.to_datetime(df["open_time"], utc=True)
    idx = opens.searchsorted(target, side="right") - 1
    if idx < 0:
        idx = 0
    if idx >= len(df):
        idx = len(df) - 1
    return _to_unix(df.iloc[idx]["open_time"])


def build_chart_payload(
    df_15m: pd.DataFrame,
    result: BacktestResult,
    *,
    symbol: str = "BTCUSDT",
    max_bars: int | None = None,
) -> dict[str, Any]:
    df, trades = _prepare_frame(df_15m, result, max_bars)
    s = result.summary()

    candles = []
    volumes = []
    for _, row in df.iterrows():
        t = _to_unix(row["open_time"])
        o, h, l, c = float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])
        candles.append({"time": t, "open": o, "high": h, "low": l, "close": c})
        vol = float(row["volume"]) if "volume" in row and pd.notna(row["volume"]) else 0.0
        volumes.append(
            {
                "time": t,
                "value": vol,
                "color": "rgba(38,166,154,0.5)" if c >= o else "rgba(239,83,80,0.5)",
            }
        )

    markers: list[dict[str, Any]] = []
    for i, tr in enumerate(trades):
        stop_s = f"{tr.stop:.4g}" if tr.stop is not None else "—"
        tp_s = f"{tr.tp:.4g}" if tr.tp is not None else "—"
        sk = getattr(tr, "stop_kind", "") or ""
        base = (
            f"#{i+1} {tr.side.upper()} | entry {tr.entry:.4g} | stop {stop_s} ({sk}) | tp {tp_s}"
        )
        et = _nearest_bar_time(df, tr.entry_time)
        if et is not None:
            if tr.side == "long":
                markers.append(
                    {
                        "time": et,
                        "position": "belowBar",
                        "color": "#089981",
                        "shape": "arrowUp",
                        "text": f"L{i+1}",
                        "size": 1.5,
                    }
                )
            else:
                markers.append(
                    {
                        "time": et,
                        "position": "aboveBar",
                        "color": "#f23645",
                        "shape": "arrowDown",
                        "text": f"S{i+1}",
                        "size": 1.5,
                    }
                )
        if tr.exit_time is not None and tr.exit is not None:
            xt = _nearest_bar_time(df, tr.exit_time)
            if xt is not None:
                col = "#089981" if tr.pnl >= 0 else "#f23645"
                markers.append(
                    {
                        "time": xt,
                        "position": "aboveBar" if tr.side == "long" else "belowBar",
                        "color": col,
                        "shape": "circle",
                        "text": f"X{i+1} {tr.exit_reason} {tr.pnl:+.1f}",
                        "size": 1.2,
                    }
                )

    # sort markers by time (library requirement)
    markers.sort(key=lambda m: (m["time"], m.get("text", "")))

    equity = []
    for ts, val in result.equity_curve:
        if len(df) and pd.Timestamp(ts) < pd.Timestamp(df["open_time"].iloc[0]):
            continue
        equity.append({"time": _to_unix(ts), "value": float(val)})
    # lightweight-charts line series needs unique ascending times
    if equity:
        dedup: dict[int, float] = {}
        for p in equity:
            dedup[p["time"]] = p["value"]
        equity = [{"time": k, "value": dedup[k]} for k in sorted(dedup)]

    trade_cards = []
    for i, tr in enumerate(trades):
        trade_cards.append(
            {
                "id": i + 1,
                "side": tr.side,
                "entry": tr.entry,
                "exit": tr.exit,
                "stop": tr.stop,
                "tp": tr.tp,
                "pnl": round(tr.pnl, 2),
                "r": round(tr.r_multiple, 2),
                "reason": tr.exit_reason,
                "entry_time": str(tr.entry_time),
                "exit_time": str(tr.exit_time),
                "stop_kind": getattr(tr, "stop_kind", ""),
                "stake": tr.stake,
                "leverage": tr.leverage,
            }
        )

    return {
        "symbol": symbol,
        "title": (
            f"{symbol} · hooks paper · trades={s['trades']} · "
            f"win={s['win_rate']:.0%} · avgR={s['avg_r']} · ret={s['return_pct']}%"
        ),
        "summary": s,
        "candles": candles,
        "volumes": volumes,
        "markers": markers,
        "equity": equity,
        "start_equity": result.starting_equity,
        "trades": trade_cards,
        "timezone": "Europe/Moscow",
    }


def render_tv_html(payload: dict[str, Any]) -> str:
    """Standalone HTML using TradingView Lightweight Charts."""
    data_json = json.dumps(payload, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{payload.get("symbol", "chart")} — TradingView style</title>
  <script src="https://unpkg.com/lightweight-charts@4.2.1/dist/lightweight-charts.standalone.production.js"></script>
  <style>
    :root {{
      --bg: #131722;
      --panel: #1e222d;
      --border: #2a2e39;
      --text: #d1d4dc;
      --muted: #787b86;
      --green: #089981;
      --red: #f23645;
      --blue: #2962ff;
    }}
    * {{ box-sizing: border-box; }}
    html, body {{
      margin: 0; padding: 0; height: 100%;
      background: var(--bg); color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Trebuchet MS", Roboto, Ubuntu, sans-serif;
    }}
    #app {{ display: flex; flex-direction: column; height: 100vh; }}
    header {{
      display: flex; flex-wrap: wrap; align-items: center; gap: 12px 20px;
      padding: 10px 16px; border-bottom: 1px solid var(--border); background: var(--panel);
    }}
    header h1 {{ font-size: 15px; font-weight: 600; margin: 0; letter-spacing: 0.2px; }}
    header .meta {{ color: var(--muted); font-size: 12px; }}
    .stats {{ display: flex; gap: 14px; flex-wrap: wrap; font-size: 12px; }}
    .stats span b {{ color: var(--text); font-weight: 600; }}
    .pos {{ color: var(--green); }}
    .neg {{ color: var(--red); }}
    #charts {{ flex: 1; display: flex; flex-direction: column; min-height: 0; }}
    #price {{ flex: 3; min-height: 280px; }}
    #vol {{ flex: 0 0 90px; border-top: 1px solid var(--border); }}
    #eq {{ flex: 0 0 120px; border-top: 1px solid var(--border); }}
    #side {{
      max-height: 160px; overflow: auto; border-top: 1px solid var(--border);
      background: var(--panel); font-size: 12px;
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 6px 10px; text-align: left; border-bottom: 1px solid var(--border); white-space: nowrap; }}
    th {{ color: var(--muted); font-weight: 500; position: sticky; top: 0; background: var(--panel); }}
    .hint {{
      padding: 6px 16px; font-size: 11px; color: var(--muted); border-top: 1px solid var(--border);
    }}
    .hint kbd {{
      background: #2a2e39; padding: 1px 5px; border-radius: 3px; color: var(--text);
    }}
  </style>
</head>
<body>
  <div id="app">
    <header>
      <h1 id="title">Chart</h1>
      <div class="meta">время оси: <b>Москва (MSK)</b> · данные UTC</div>
      <div class="stats" id="stats"></div>
    </header>
    <div id="charts">
      <div id="price"></div>
      <div id="vol"></div>
      <div id="eq"></div>
    </div>
    <div id="side">
      <table>
        <thead>
          <tr>
            <th>#</th><th>Side</th><th>Entry</th><th>Exit</th><th>Stop</th><th>TP</th>
            <th>PnL</th><th>R</th><th>Reason</th><th>Entry time (UTC)</th>
          </tr>
        </thead>
        <tbody id="trades-body"></tbody>
      </table>
    </div>
    <div class="hint">
      Как в TradingView:
      <kbd>скролл</kbd> зум ·
      <kbd>drag</kbd> панорама ·
      <kbd>зажать</kbd> крест ·
      ▲ long / ▼ short / ● exit ·
      красная линия = stop/liq · бирюзовая = TP
    </div>
  </div>
  <script>
    const DATA = {data_json};

    document.getElementById('title').textContent = DATA.title;
    const s = DATA.summary || {{}};
    const pnlClass = (s.total_pnl || 0) >= 0 ? 'pos' : 'neg';
    document.getElementById('stats').innerHTML = `
      <span>trades <b>${{s.trades ?? '—'}}</b></span>
      <span>win <b>${{((s.win_rate||0)*100).toFixed(0)}}%</b></span>
      <span>avgR <b>${{s.avg_r ?? '—'}}</b></span>
      <span class="${{pnlClass}}">pnl <b>${{(s.total_pnl??0).toFixed(2)}}</b> (${{(s.return_pct??0).toFixed(2)}}%)</span>
    `;

    const tb = document.getElementById('trades-body');
    (DATA.trades || []).forEach(t => {{
      const pc = t.pnl >= 0 ? 'pos' : 'neg';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${{t.id}}</td>
        <td class="${{t.side==='long'?'pos':'neg'}}">${{t.side}}</td>
        <td>${{t.entry?.toFixed?.(4) ?? t.entry}}</td>
        <td>${{t.exit?.toFixed?.(4) ?? t.exit ?? '—'}}</td>
        <td>${{t.stop?.toFixed?.(4) ?? '—'}} <span style="color:var(--muted);font-size:10px">${{t.stop_kind||''}}</span></td>
        <td>${{t.tp?.toFixed?.(4) ?? '—'}}</td>
        <td class="${{pc}}">${{t.pnl?.toFixed?.(2)}}</td>
        <td class="${{pc}}">${{t.r}}</td>
        <td>${{t.reason || '—'}}</td>
        <td style="color:var(--muted)">${{t.entry_time || ''}}</td>`;
      tb.appendChild(tr);
    }});

    const tvTheme = {{
      layout: {{
        background: {{ type: 'solid', color: '#131722' }},
        textColor: '#d1d4dc',
        fontSize: 12,
      }},
      grid: {{
        vertLines: {{ color: '#1e222d' }},
        horzLines: {{ color: '#1e222d' }},
      }},
      crosshair: {{
        mode: LightweightCharts.CrosshairMode.Normal,
        vertLine: {{ color: '#758696', labelBackgroundColor: '#2962ff' }},
        horzLine: {{ color: '#758696', labelBackgroundColor: '#2962ff' }},
      }},
      rightPriceScale: {{ borderColor: '#2a2e39' }},
      timeScale: {{
        borderColor: '#2a2e39',
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 6,
        barSpacing: 8,
      }},
      localization: {{
        locale: 'ru-RU',
        timeFormatter: (ts) => {{
          const d = new Date(ts * 1000);
          return d.toLocaleString('ru-RU', {{
            timeZone: 'Europe/Moscow',
            day: '2-digit', month: '2-digit',
            hour: '2-digit', minute: '2-digit',
            hour12: false,
          }});
        }},
      }},
    }};

    const priceEl = document.getElementById('price');
    const volEl = document.getElementById('vol');
    const eqEl = document.getElementById('eq');

    const priceChart = LightweightCharts.createChart(priceEl, {{
      ...tvTheme,
      height: priceEl.clientHeight,
      width: priceEl.clientWidth,
    }});
    const candleSeries = priceChart.addCandlestickSeries({{
      upColor: '#089981',
      downColor: '#f23645',
      borderUpColor: '#089981',
      borderDownColor: '#f23645',
      wickUpColor: '#089981',
      wickDownColor: '#f23645',
    }});
    candleSeries.setData(DATA.candles || []);
    if (DATA.markers && DATA.markers.length) {{
      candleSeries.setMarkers(DATA.markers);
    }}

    // Price lines for last few trade levels (TV-style)
    (DATA.trades || []).slice(-8).forEach(t => {{
      if (t.stop != null) {{
        candleSeries.createPriceLine({{
          price: t.stop,
          color: 'rgba(242,54,69,0.55)',
          lineWidth: 1,
          lineStyle: LightweightCharts.LineStyle.Dashed,
          axisLabelVisible: true,
          title: `SL/Liq #${{t.id}}`,
        }});
      }}
      if (t.tp != null) {{
        candleSeries.createPriceLine({{
          price: t.tp,
          color: 'rgba(8,153,129,0.55)',
          lineWidth: 1,
          lineStyle: LightweightCharts.LineStyle.Dashed,
          axisLabelVisible: true,
          title: `TP #${{t.id}}`,
        }});
      }}
    }});

    const volChart = LightweightCharts.createChart(volEl, {{
      ...tvTheme,
      height: volEl.clientHeight,
      width: volEl.clientWidth,
      timeScale: {{ ...tvTheme.timeScale, visible: false }},
    }});
    const volSeries = volChart.addHistogramSeries({{
      priceFormat: {{ type: 'volume' }},
      priceScaleId: '',
    }});
    volSeries.priceScale().applyOptions({{ scaleMargins: {{ top: 0.1, bottom: 0 }} }});
    volSeries.setData(DATA.volumes || []);

    const eqChart = LightweightCharts.createChart(eqEl, {{
      ...tvTheme,
      height: eqEl.clientHeight,
      width: eqEl.clientWidth,
    }});
    const eqSeries = eqChart.addAreaSeries({{
      lineColor: '#2962ff',
      topColor: 'rgba(41,98,255,0.35)',
      bottomColor: 'rgba(41,98,255,0.02)',
      lineWidth: 2,
    }});
    if (DATA.equity && DATA.equity.length) {{
      eqSeries.setData(DATA.equity);
      eqSeries.createPriceLine({{
        price: DATA.start_equity,
        color: 'rgba(120,123,134,0.8)',
        lineWidth: 1,
        lineStyle: LightweightCharts.LineStyle.Dotted,
        axisLabelVisible: true,
        title: 'start',
      }});
    }}

    // Sync time scales (TV multi-pane feel)
    function sync(source, targets) {{
      source.timeScale().subscribeVisibleLogicalRangeChange(range => {{
        if (!range) return;
        targets.forEach(t => {{
          try {{ t.timeScale().setVisibleLogicalRange(range); }} catch (e) {{}}
        }});
      }});
    }}
    sync(priceChart, [volChart, eqChart]);
    sync(volChart, [priceChart, eqChart]);
    sync(eqChart, [priceChart, volChart]);

    priceChart.timeScale().fitContent();

    function resize() {{
      priceChart.applyOptions({{ width: priceEl.clientWidth, height: priceEl.clientHeight }});
      volChart.applyOptions({{ width: volEl.clientWidth, height: volEl.clientHeight }});
      eqChart.applyOptions({{ width: eqEl.clientWidth, height: eqEl.clientHeight }});
    }}
    window.addEventListener('resize', resize);
    new ResizeObserver(resize).observe(document.getElementById('charts'));
  </script>
</body>
</html>
"""


def plot_backtest(
    df_15m: pd.DataFrame,
    result: BacktestResult,
    *,
    symbol: str = "BTCUSDT",
    title: str | None = None,
    max_bars: int | None = None,
) -> dict[str, Any]:
    """Build chart payload (TradingView Lightweight Charts)."""
    payload = build_chart_payload(df_15m, result, symbol=symbol, max_bars=max_bars)
    if title:
        payload["title"] = title
    return payload


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
    payload = plot_backtest(df_15m, result, symbol=symbol, max_bars=max_bars)
    html = render_tv_html(payload)
    path.write_text(html, encoding="utf-8")
    if open_browser:
        import webbrowser

        webbrowser.open(path.resolve().as_uri())
    return path
