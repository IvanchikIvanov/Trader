"""Paper backtest engine — simulated equity, no exchange orders."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

from trader.hooks import HookSignal, scan_hooks

ExitReason = Literal["tp", "sl", "structure", "eod", "timeout"]


@dataclass
class Trade:
    side: str
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp | None
    entry: float
    stop: float
    tp: float
    exit: float | None
    size: float  # units (contracts/coins notional base)
    risk_amount: float
    pnl: float = 0.0
    r_multiple: float = 0.0
    exit_reason: ExitReason | None = None
    symbol: str = ""


@dataclass
class BacktestResult:
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[tuple[pd.Timestamp, float]] = field(default_factory=list)
    starting_equity: float = 10_000.0
    ending_equity: float = 10_000.0

    @property
    def total_pnl(self) -> float:
        return self.ending_equity - self.starting_equity

    @property
    def n_trades(self) -> int:
        return len(self.trades)

    @property
    def win_rate(self) -> float:
        closed = [t for t in self.trades if t.exit is not None]
        if not closed:
            return 0.0
        wins = sum(1 for t in closed if t.pnl > 0)
        return wins / len(closed)

    @property
    def avg_r(self) -> float:
        closed = [t for t in self.trades if t.exit is not None]
        if not closed:
            return 0.0
        return sum(t.r_multiple for t in closed) / len(closed)

    def summary(self) -> dict:
        return {
            "trades": self.n_trades,
            "win_rate": round(self.win_rate, 4),
            "avg_r": round(self.avg_r, 3),
            "starting_equity": self.starting_equity,
            "ending_equity": round(self.ending_equity, 2),
            "total_pnl": round(self.total_pnl, 2),
            "return_pct": round(100.0 * self.total_pnl / self.starting_equity, 2),
        }


@dataclass
class BacktestConfig:
    starting_equity: float = 10_000.0
    risk_pct: float = 0.005  # 0.5% per trade paper default
    rr_target: float = 2.0  # 1:2
    stop_buffer_pct: float = 0.0005
    require_htf_bias: bool = True
    one_position: bool = True
    max_bars_in_trade: int = 96  # 15m * 96 = 24h safety flat


def _position_size(equity: float, risk_pct: float, risk_per_unit: float) -> float:
    if risk_per_unit <= 0:
        return 0.0
    risk_amount = equity * risk_pct
    return risk_amount / risk_per_unit


def run_backtest(
    df_15m: pd.DataFrame,
    df_1h: pd.DataFrame | None = None,
    df_4h: pd.DataFrame | None = None,
    *,
    symbol: str = "BTCUSDT",
    config: BacktestConfig | None = None,
) -> BacktestResult:
    cfg = config or BacktestConfig()
    signals = scan_hooks(
        df_15m,
        df_1h,
        df_4h,
        stop_buffer_pct=cfg.stop_buffer_pct,
        require_htf_bias=cfg.require_htf_bias,
    )
    by_index = {s.index: s for s in signals}

    equity = cfg.starting_equity
    result = BacktestResult(starting_equity=cfg.starting_equity, ending_equity=equity)
    result.equity_curve.append((df_15m.iloc[0]["open_time"], equity))

    open_trade: Trade | None = None
    entry_index: int | None = None

    for i in range(len(df_15m)):
        bar = df_15m.iloc[i]
        high = float(bar["high"])
        low = float(bar["low"])
        close = float(bar["close"])
        t = bar["close_time"]

        # manage open position on this bar (after entry bar)
        if open_trade is not None and entry_index is not None and i > entry_index:
            exit_px, reason = _check_exit(open_trade, high, low, close, bars_held=i - entry_index, cfg=cfg)
            if exit_px is not None and reason is not None:
                _close_trade(open_trade, exit_px, t, reason)
                equity += open_trade.pnl
                result.trades.append(open_trade)
                result.equity_curve.append((t, equity))
                open_trade = None
                entry_index = None

        # new signal on closed bar — enter at close (same as rules)
        if open_trade is None and i in by_index:
            sig: HookSignal = by_index[i]
            size = _position_size(equity, cfg.risk_pct, sig.risk_per_unit)
            if size <= 0:
                continue
            if sig.side == "long":
                tp = sig.entry + cfg.rr_target * sig.risk_per_unit
            else:
                tp = sig.entry - cfg.rr_target * sig.risk_per_unit
            open_trade = Trade(
                side=sig.side,
                entry_time=sig.time,
                exit_time=None,
                entry=sig.entry,
                stop=sig.stop,
                tp=tp,
                exit=None,
                size=size,
                risk_amount=equity * cfg.risk_pct,
                symbol=symbol,
            )
            entry_index = i
            if not cfg.one_position:
                pass  # reserved

    # force flat at end of series (paper EOD)
    if open_trade is not None and entry_index is not None:
        last = df_15m.iloc[-1]
        _close_trade(open_trade, float(last["close"]), last["close_time"], "eod")
        equity += open_trade.pnl
        result.trades.append(open_trade)
        result.equity_curve.append((last["close_time"], equity))

    result.ending_equity = equity
    return result


def _check_exit(
    trade: Trade,
    high: float,
    low: float,
    close: float,
    *,
    bars_held: int,
    cfg: BacktestConfig,
) -> tuple[float | None, ExitReason | None]:
    if bars_held >= cfg.max_bars_in_trade:
        return close, "timeout"

    if trade.side == "long":
        # conservative: stop before tp if both touched
        if low <= trade.stop:
            return trade.stop, "sl"
        if high >= trade.tp:
            return trade.tp, "tp"
        # structure = stop already is hook low
    else:
        if high >= trade.stop:
            return trade.stop, "sl"
        if low <= trade.tp:
            return trade.tp, "tp"
    return None, None


def _close_trade(trade: Trade, exit_px: float, exit_time: pd.Timestamp, reason: ExitReason) -> None:
    trade.exit = exit_px
    trade.exit_time = exit_time
    trade.exit_reason = reason
    if trade.side == "long":
        trade.pnl = (exit_px - trade.entry) * trade.size
    else:
        trade.pnl = (trade.entry - exit_px) * trade.size
    risk = trade.risk_amount if trade.risk_amount else 1.0
    trade.r_multiple = trade.pnl / risk
