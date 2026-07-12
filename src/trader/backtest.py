"""Paper backtest engine — simulated equity, no exchange orders."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

from trader.hooks import HookSignal, scan_hooks

ExitReason = Literal["tp", "sl", "liq", "structure", "eod", "timeout"]
StopKind = Literal["hook", "liquidation", "none"]
TpKind = Literal["hook_rr", "liq_rr", "pct", "none"]


@dataclass
class Trade:
    side: str
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp | None
    entry: float
    stop: float | None
    tp: float | None
    exit: float | None
    size: float  # base units (coins)
    risk_amount: float  # reference for R (stake or equity*risk%)
    notional: float = 0.0
    leverage: float = 1.0
    stake: float = 0.0
    stop_kind: StopKind = "hook"
    tp_kind: TpKind = "hook_rr"
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
    risk_pct: float = 0.005  # used when stake_usd is None
    # TP: hook_rr → entry ± rr * hook_range; liq_rr → entry ± rr * |entry-liq|;
    # pct → entry * (1 ± tp_pct)
    rr_target: float = 1.0  # stake+lev: 1× dist-to-liq (+10% @ 10x); hook mode: 1× hook range
    tp_pct: float | None = None  # if set, overrides rr (e.g. 0.03 = +3%)
    stop_buffer_pct: float = 0.0005
    require_htf_bias: bool = True
    one_position: bool = True
    max_bars_in_trade: int = 96  # 15m * 96 = 24h safety flat
    # Fixed-stake mode (margin)
    stake_usd: float | None = None  # e.g. 30
    leverage: float = 1.0  # e.g. 10 → notional = stake * leverage
    use_stop: bool = True
    use_tp: bool = True
    # stake+leverage → stop at approx liquidation; else hook low/high
    stop_mode: Literal["auto", "hook", "liquidation", "none"] = "auto"


def liquidation_price(entry: float, side: str, leverage: float) -> float | None:
    """
    Simplified isolated liquidation: full margin lost when price moves ~1/leverage.
    long: entry * (1 - 1/lev)   short: entry * (1 + 1/lev)
    Ignores fees / maintenance margin (paper approx).
    """
    if entry <= 0 or leverage <= 1:
        return None
    frac = 1.0 / leverage
    if side == "long":
        return entry * (1.0 - frac)
    return entry * (1.0 + frac)


def _position_size_risk(equity: float, risk_pct: float, risk_per_unit: float) -> tuple[float, float]:
    if risk_per_unit <= 0:
        return 0.0, 0.0
    risk_amount = equity * risk_pct
    return risk_amount / risk_per_unit, risk_amount


def _position_size_stake(entry: float, stake_usd: float, leverage: float) -> tuple[float, float, float]:
    if entry <= 0 or stake_usd <= 0 or leverage <= 0:
        return 0.0, 0.0, 0.0
    notional = stake_usd * leverage
    size = notional / entry
    return size, notional, stake_usd


def _resolve_stop(
    sig: HookSignal,
    cfg: BacktestConfig,
) -> tuple[float | None, StopKind]:
    if not cfg.use_stop or cfg.stop_mode == "none":
        return None, "none"

    mode = cfg.stop_mode
    if mode == "auto":
        if cfg.stake_usd is not None and cfg.leverage > 1:
            mode = "liquidation"
        else:
            mode = "hook"

    if mode == "liquidation":
        liq = liquidation_price(sig.entry, sig.side, cfg.leverage)
        return liq, "liquidation"
    return sig.stop, "hook"


def _resolve_tp(
    sig: HookSignal,
    cfg: BacktestConfig,
    stop: float | None,
    stop_kind: StopKind,
) -> tuple[float | None, TpKind]:
    if not cfg.use_tp:
        return None, "none"

    # Explicit % of price wins
    if cfg.tp_pct is not None and cfg.tp_pct > 0:
        if sig.side == "long":
            return sig.entry * (1.0 + cfg.tp_pct), "pct"
        return sig.entry * (1.0 - cfg.tp_pct), "pct"

    # Wider take: prefer distance to liquidation when that is the stop
    if stop is not None and stop_kind == "liquidation":
        r_unit = abs(sig.entry - stop)
        if r_unit > 0:
            if sig.side == "long":
                return sig.entry + cfg.rr_target * r_unit, "liq_rr"
            return sig.entry - cfg.rr_target * r_unit, "liq_rr"

    # Fallback: hook range × rr
    if sig.risk_per_unit > 0:
        if sig.side == "long":
            return sig.entry + cfg.rr_target * sig.risk_per_unit, "hook_rr"
        return sig.entry - cfg.rr_target * sig.risk_per_unit, "hook_rr"
    return None, "none"


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

        if open_trade is not None and entry_index is not None and i > entry_index:
            exit_px, reason = _check_exit(
                open_trade, high, low, close, bars_held=i - entry_index, cfg=cfg
            )
            if exit_px is not None and reason is not None:
                _close_trade(open_trade, exit_px, t, reason)
                equity += open_trade.pnl
                result.trades.append(open_trade)
                result.equity_curve.append((t, equity))
                open_trade = None
                entry_index = None

        if open_trade is None and i in by_index:
            sig: HookSignal = by_index[i]
            if cfg.stake_usd is not None:
                size, notional, stake = _position_size_stake(
                    sig.entry, cfg.stake_usd, cfg.leverage
                )
                risk_amount = stake
                lev = cfg.leverage
            else:
                size, risk_amount = _position_size_risk(
                    equity, cfg.risk_pct, sig.risk_per_unit
                )
                notional = size * sig.entry
                stake = risk_amount
                lev = 1.0

            if size <= 0:
                continue

            stop, stop_kind = _resolve_stop(sig, cfg)
            tp, tp_kind = _resolve_tp(sig, cfg, stop, stop_kind)

            open_trade = Trade(
                side=sig.side,
                entry_time=sig.time,
                exit_time=None,
                entry=sig.entry,
                stop=stop,
                tp=tp,
                exit=None,
                size=size,
                risk_amount=risk_amount,
                notional=notional,
                leverage=lev,
                stake=stake,
                stop_kind=stop_kind,
                tp_kind=tp_kind,
                symbol=symbol,
            )
            entry_index = i

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
        if cfg.use_stop and trade.stop is not None and low <= trade.stop:
            reason: ExitReason = "liq" if trade.stop_kind == "liquidation" else "sl"
            return trade.stop, reason
        if cfg.use_tp and trade.tp is not None and high >= trade.tp:
            return trade.tp, "tp"
    else:
        if cfg.use_stop and trade.stop is not None and high >= trade.stop:
            reason = "liq" if trade.stop_kind == "liquidation" else "sl"
            return trade.stop, reason
        if cfg.use_tp and trade.tp is not None and low <= trade.tp:
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
    # Cap loss at -stake for liq (can't lose more than margin in this model)
    if reason == "liq" and trade.stake > 0:
        trade.pnl = max(trade.pnl, -trade.stake)
    risk = trade.risk_amount if trade.risk_amount else 1.0
    trade.r_multiple = trade.pnl / risk
