"""CLI: python -m trader backtest --symbol BTCUSDT --days 30"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from trader.backtest import BacktestConfig, run_backtest
from trader.data import fetch_klines


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Paper backtest крючки (no deposit)")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("backtest", help="Run historical paper backtest")
    b.add_argument("--symbol", default="BTCUSDT", help="BTCUSDT or ETHUSDT")
    b.add_argument("--days", type=int, default=30, help="Lookback days")
    b.add_argument("--equity", type=float, default=10_000.0)
    b.add_argument("--risk-pct", type=float, default=0.005, help="Risk per trade, e.g. 0.005 = 0.5%%")
    b.add_argument("--rr", type=float, default=2.0, help="Take profit R multiple (2 = 1:2)")
    b.add_argument("--no-htf", action="store_true", help="Ignore 1h/4h bias filter")
    b.add_argument("--csv-out", type=Path, default=None, help="Write trades CSV")
    b.add_argument(
        "--chart",
        type=Path,
        nargs="?",
        const=Path("charts/backtest.html"),
        default=None,
        help="Write interactive HTML chart (default path: charts/backtest.html)",
    )
    b.add_argument(
        "--chart-bars",
        type=int,
        default=None,
        help="Only plot last N 15m bars (easier to tune; trades outside window hidden)",
    )
    b.add_argument(
        "--open",
        action="store_true",
        help="Open chart in browser after save",
    )

    lab = sub.add_parser("labels", help="Audit human gold hooks vs detector")
    lab.add_argument(
        "--file",
        type=Path,
        default=Path("labels/hooks_gold.csv"),
        help="CSV with human labels",
    )

    args = p.parse_args(argv)
    if args.cmd == "backtest":
        return cmd_backtest(args)
    if args.cmd == "labels":
        return cmd_labels(args)
    return 1


def cmd_labels(args: argparse.Namespace) -> int:
    from trader.labels import audit_labels

    path = args.file
    if not path.exists():
        print(f"File not found: {path}")
        return 1
    print(f"Auditing {path} …")
    rows = audit_labels(path)
    hits = misses = false_pos = ok_rej = nobar = 0
    for r in rows:
        print(
            f"  {r['verdict']:10} {r['symbol']} {r['side']:5} {r['time_utc']} "
            f"detected={r['detected']} bar={r['bar_found']}  {r.get('note','')}"
        )
        v = r["verdict"]
        if v == "HIT":
            hits += 1
        elif v == "MISS":
            misses += 1
        elif v == "FALSE_POS":
            false_pos += 1
        elif v == "OK_REJECT":
            ok_rej += 1
        elif v == "NO_BAR":
            nobar += 1
    print(
        f"\nSummary: HIT={hits} MISS={misses} FALSE_POS={false_pos} "
        f"OK_REJECT={ok_rej} NO_BAR={nobar}"
    )
    if misses:
        print("MISS = you marked gold, detector skipped → relax/fix rules")
    if false_pos:
        print("FALSE_POS = you rejected, detector fired → tighten rules")
    return 0


def cmd_backtest(args: argparse.Namespace) -> int:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=args.days)
    print(f"Fetching {args.symbol} 15m/1h/4h from Binance futures (public)…")
    print(f"Range: {start.date()} → {end.date()}  |  paper equity={args.equity}")

    df_15 = fetch_klines(args.symbol, "15m", start=start, end=end)
    df_1h = fetch_klines(args.symbol, "1h", start=start, end=end)
    df_4h = fetch_klines(args.symbol, "4h", start=start, end=end)
    print(f"Bars 15m={len(df_15)} 1h={len(df_1h)} 4h={len(df_4h)}")

    cfg = BacktestConfig(
        starting_equity=args.equity,
        risk_pct=args.risk_pct,
        rr_target=args.rr,
        require_htf_bias=not args.no_htf,
    )
    result = run_backtest(df_15, df_1h, df_4h, symbol=args.symbol, config=cfg)
    s = result.summary()
    print("\n=== PAPER BACKTEST RESULT (no real money) ===")
    for k, v in s.items():
        print(f"  {k}: {v}")

    if result.trades:
        print("\nLast trades:")
        for t in result.trades[-8:]:
            print(
                f"  {t.side:5} {t.entry_time} → {t.exit_time}  "
                f"pnl={t.pnl:+.2f} R={t.r_multiple:+.2f} ({t.exit_reason})"
            )

    if args.csv_out:
        import pandas as pd

        rows = [
            {
                "symbol": t.symbol,
                "side": t.side,
                "entry_time": t.entry_time,
                "exit_time": t.exit_time,
                "entry": t.entry,
                "stop": t.stop,
                "tp": t.tp,
                "exit": t.exit,
                "pnl": t.pnl,
                "r": t.r_multiple,
                "reason": t.exit_reason,
            }
            for t in result.trades
        ]
        args.csv_out.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(args.csv_out, index=False)
        print(f"\nWrote {args.csv_out}")

    chart_path = args.chart
    if chart_path is None:
        # default: always write chart for visual tuning
        chart_path = Path("charts") / f"{args.symbol.lower()}_{args.days}d.html"
    from trader.chart import save_chart

    out = save_chart(
        df_15,
        result,
        chart_path,
        symbol=args.symbol,
        max_bars=args.chart_bars,
        open_browser=args.open,
    )
    print(f"\nChart: {out.resolve()}")
    print("  ▲ green = long entry · ▼ red = short entry · ✕ = exit")
    print("  dashed red = stop · dashed teal = TP · zoom with rangeslider")

    print("\nReminder: this is simulation only. Fees/slippage not fully modeled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
