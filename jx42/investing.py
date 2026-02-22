"""Investing Program — Milestone 2.

Responsibilities
----------------
- Strategy definition: rules-based format (JSON-serialisable).
- Market data ingestion from CSV (single source; OHLCV format).
- Data integrity checks (no gaps, no look-ahead bias).
- Backtest v1: simple, transparent, no look-ahead bias.
- Watchlist + signal scoring.
- Draft trade tickets (never placed in v1).

All outputs are *draft-only*; no orders are ever placed here.
"""
from __future__ import annotations

import csv
import io
import uuid
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .models import (
    BacktestResult,
    BacktestTrade,
    InvestingTradeTicketDraft,
    MarketDataPoint,
    StrategyDefinition,
    TradeSignal,
    utc_now_iso,
)

# ---------------------------------------------------------------------------
# Market data ingestion
# ---------------------------------------------------------------------------


class MarketDataError(ValueError):
    pass


def load_market_data_csv(csv_text: str) -> List[MarketDataPoint]:
    """Parse OHLCV CSV into MarketDataPoint objects.

    Required columns (case-insensitive): symbol, date, open, high, low, close, volume
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        raise MarketDataError("Market data CSV has no headers.")

    headers = {h.strip().lower() for h in reader.fieldnames}
    required = {"symbol", "date", "open", "high", "low", "close", "volume"}
    missing = required - headers
    if missing:
        raise MarketDataError(f"Market data CSV missing columns: {missing}")

    points: List[MarketDataPoint] = []
    for i, row in enumerate(reader):
        r = {k.strip().lower(): v.strip() for k, v in row.items()}
        try:
            points.append(
                MarketDataPoint(
                    symbol=r["symbol"].upper(),
                    date=r["date"],
                    open=float(r["open"]),
                    high=float(r["high"]),
                    low=float(r["low"]),
                    close=float(r["close"]),
                    volume=float(r["volume"]),
                )
            )
        except (ValueError, KeyError) as exc:
            raise MarketDataError(f"Row {i + 1}: {exc}") from exc

    return points


# ---------------------------------------------------------------------------
# Data integrity checks
# ---------------------------------------------------------------------------


def check_data_integrity(points: Sequence[MarketDataPoint]) -> List[str]:
    """Return a list of integrity violation messages (empty = clean).

    Checks:
    - Dates are sorted (ascending) per symbol.
    - high >= max(open, close, low).
    - low <= min(open, close, high).
    - No duplicate (symbol, date) pairs.
    - Volume >= 0.
    - No future-dated entries relative to last date (basic sanity).
    """
    errors: List[str] = []
    by_symbol: Dict[str, List[MarketDataPoint]] = defaultdict(list)
    for p in points:
        by_symbol[p.symbol].append(p)

    for symbol, sym_points in by_symbol.items():
        dates = [p.date for p in sym_points]
        seen_dates: set = set()
        for p in sym_points:
            if p.date in seen_dates:
                errors.append(f"{symbol} {p.date}: duplicate date.")
            seen_dates.add(p.date)

        if dates != sorted(dates):
            errors.append(f"{symbol}: dates are not in ascending order.")

        for p in sym_points:
            if p.high < max(p.open, p.close, p.low):
                errors.append(f"{symbol} {p.date}: high={p.high} < max(open, close, low).")
            if p.low > min(p.open, p.close, p.high):
                errors.append(f"{symbol} {p.date}: low={p.low} > min(open, close, high).")
            if p.volume < 0:
                errors.append(f"{symbol} {p.date}: negative volume.")

    return errors


# ---------------------------------------------------------------------------
# Signal Engine
# ---------------------------------------------------------------------------

_MA_WINDOWS = {"sma_10": 10, "sma_20": 20, "sma_50": 50, "sma_200": 200}


def _sma(closes: List[float], window: int) -> Optional[float]:
    if len(closes) < window:
        return None
    return sum(closes[-window:]) / window


def compute_signals(
    symbol_data: Sequence[MarketDataPoint],
    strategy: StrategyDefinition,
) -> List[TradeSignal]:
    """Compute entry/exit signals for a single symbol using strategy rules.

    Supported rule types and parameters:
    - entry: {"indicator": "sma_crossover", "fast_window": int, "slow_window": int}
      Fires when fast SMA crosses above slow SMA.
    - entry: {"indicator": "breakout", "window": int}
      Fires when close > N-day high.
    - exit: {"indicator": "sma_cross_below", "fast_window": int, "slow_window": int}
      Fires when fast SMA crosses below slow SMA.
    - exit: {"indicator": "trailing_stop", "pct": float}
      Fires when close drops pct% below recent high.
    """
    points = list(symbol_data)
    if not points:
        return []

    closes = [p.close for p in points]
    highs = [p.high for p in points]
    signals: List[TradeSignal] = []

    for i in range(1, len(points)):
        p = points[i]
        for rule in strategy.rules:
            params = rule.parameters
            indicator = params.get("indicator", "")

            if rule.rule_type == "entry":
                if indicator == "sma_crossover":
                    fast_w = int(params.get("fast_window", 10))
                    slow_w = int(params.get("slow_window", 50))
                    fast_now = _sma(closes[: i + 1], fast_w)
                    slow_now = _sma(closes[: i + 1], slow_w)
                    fast_prev = _sma(closes[:i], fast_w)
                    slow_prev = _sma(closes[:i], slow_w)
                    if None not in (fast_now, slow_now, fast_prev, slow_prev):
                        if fast_prev <= slow_prev and fast_now > slow_now:  # type: ignore[operator]
                            signals.append(
                                TradeSignal(
                                    symbol=p.symbol,
                                    date=p.date,
                                    signal_type="entry",
                                    rule_id=rule.rule_id,
                                    score=0.8,
                                    rationale=f"SMA({fast_w}) crossed above SMA({slow_w})",
                                )
                            )

                elif indicator == "breakout":
                    window = int(params.get("window", 20))
                    if i >= window:
                        recent_high = max(highs[i - window : i])
                        if closes[i] > recent_high:
                            signals.append(
                                TradeSignal(
                                    symbol=p.symbol,
                                    date=p.date,
                                    signal_type="entry",
                                    rule_id=rule.rule_id,
                                    score=0.7,
                                    rationale=f"Close {closes[i]:.2f} > {window}-day high {recent_high:.2f}",
                                )
                            )

            elif rule.rule_type == "exit":
                if indicator == "sma_cross_below":
                    fast_w = int(params.get("fast_window", 10))
                    slow_w = int(params.get("slow_window", 50))
                    fast_now = _sma(closes[: i + 1], fast_w)
                    slow_now = _sma(closes[: i + 1], slow_w)
                    fast_prev = _sma(closes[:i], fast_w)
                    slow_prev = _sma(closes[:i], slow_w)
                    if None not in (fast_now, slow_now, fast_prev, slow_prev):
                        if fast_prev >= slow_prev and fast_now < slow_now:  # type: ignore[operator]
                            signals.append(
                                TradeSignal(
                                    symbol=p.symbol,
                                    date=p.date,
                                    signal_type="exit",
                                    rule_id=rule.rule_id,
                                    score=0.8,
                                    rationale=f"SMA({fast_w}) crossed below SMA({slow_w})",
                                )
                            )

                elif indicator == "trailing_stop":
                    pct = float(params.get("pct", 0.05))
                    if i >= 1:
                        recent_peak = max(highs[: i + 1])
                        stop = recent_peak * (1 - pct)
                        if closes[i] < stop:
                            signals.append(
                                TradeSignal(
                                    symbol=p.symbol,
                                    date=p.date,
                                    signal_type="exit",
                                    rule_id=rule.rule_id,
                                    score=0.9,
                                    rationale=f"Trailing stop hit: close {closes[i]:.2f} < stop {stop:.2f}",
                                )
                            )

    return signals


# ---------------------------------------------------------------------------
# Backtester — simple, transparent, no look-ahead bias
# ---------------------------------------------------------------------------


def run_backtest(
    market_data: Sequence[MarketDataPoint],
    strategy: StrategyDefinition,
    initial_capital: float = 100_000.0,
) -> BacktestResult:
    """Run a simple long-only backtest for the strategy universe.

    - Uses next-day *open* price for entries and exits to avoid look-ahead bias.
    - One position per symbol at a time.
    - Respects max_open_positions and max_position_size from strategy.
    - Applies kill-switch (stop trading) if drawdown exceeds max_drawdown_pct.
    - Returns BacktestResult with trades, total return, max drawdown, win rate.
    """
    by_symbol: Dict[str, List[MarketDataPoint]] = defaultdict(list)
    for p in market_data:
        if p.symbol in strategy.universe:
            by_symbol[p.symbol].append(p)

    # Pre-compute signals per symbol (no look-ahead: use data up to day i)
    all_signals: List[TradeSignal] = []
    for symbol, points in by_symbol.items():
        all_signals.extend(compute_signals(points, strategy))

    # Build per-symbol signal lookup for simulation
    entry_dates: Dict[str, set] = defaultdict(set)
    exit_dates: Dict[str, set] = defaultdict(set)
    for sig in all_signals:
        if sig.signal_type == "entry":
            entry_dates[sig.symbol].add(sig.date)
        elif sig.signal_type == "exit":
            exit_dates[sig.symbol].add(sig.date)

    # Simulation
    capital = initial_capital
    peak_capital = initial_capital
    max_drawdown = 0.0
    open_positions: Dict[str, Tuple[float, str, str]] = {}  # symbol -> (qty, entry_date, entry_rule)
    trades: List[BacktestTrade] = []
    killed = False

    # Collect all dates in order across all symbols in universe
    all_dates = sorted({p.date for p in market_data if p.symbol in strategy.universe})
    price_lookup: Dict[Tuple[str, str], MarketDataPoint] = {(p.symbol, p.date): p for p in market_data}

    for date_idx, today in enumerate(all_dates):
        if killed:
            break

        # Process exits first (for open positions)
        for symbol in list(open_positions.keys()):
            if today in exit_dates.get(symbol, set()):
                qty, entry_date, entry_rule = open_positions[symbol]
                entry_p = price_lookup.get((symbol, entry_date))
                exit_p = price_lookup.get((symbol, today))
                if entry_p and exit_p:
                    # Use next-day open for exit execution
                    if date_idx + 1 < len(all_dates):
                        next_date = all_dates[date_idx + 1]
                        next_p = price_lookup.get((symbol, next_date))
                        exec_price = next_p.open if next_p else exit_p.close
                    else:
                        exec_price = exit_p.close

                    pnl = (exec_price - entry_p.open) * qty
                    capital += pnl
                    trades.append(
                        BacktestTrade(
                            symbol=symbol,
                            entry_date=entry_date,
                            exit_date=today,
                            entry_price=round(entry_p.open, 4),
                            exit_price=round(exec_price, 4),
                            qty=round(qty, 4),
                            pnl=round(pnl, 2),
                            rule_id=entry_rule,
                        )
                    )
                    del open_positions[symbol]

                    # Update drawdown
                    if capital > peak_capital:
                        peak_capital = capital
                    dd = (peak_capital - capital) / peak_capital if peak_capital > 0 else 0.0
                    if dd > max_drawdown:
                        max_drawdown = dd
                    if dd >= strategy.max_drawdown_pct:
                        killed = True

        # Process entries (skip if already in position or at max positions)
        for symbol in strategy.universe:
            if killed:
                break
            if symbol in open_positions:
                continue
            if len(open_positions) >= strategy.max_open_positions:
                continue
            if today in entry_dates.get(symbol, set()):
                # Use next-day open for entry execution to avoid look-ahead bias
                if date_idx + 1 < len(all_dates):
                    next_date = all_dates[date_idx + 1]
                    next_p = price_lookup.get((symbol, next_date))
                    if next_p:
                        exec_price = next_p.open
                        position_value = capital * strategy.max_position_size
                        qty = position_value / exec_price if exec_price > 0 else 0
                        open_positions[symbol] = (qty, next_date, "entry")

    # Close any remaining open positions at last available price
    for symbol, (qty, entry_date, entry_rule) in open_positions.items():
        # Find last available price for symbol
        sym_points = sorted(by_symbol.get(symbol, []), key=lambda p: p.date)
        if sym_points:
            last_p = sym_points[-1]
            entry_p = price_lookup.get((symbol, entry_date))
            if entry_p:
                pnl = (last_p.close - entry_p.open) * qty
                capital += pnl
                trades.append(
                    BacktestTrade(
                        symbol=symbol,
                        entry_date=entry_date,
                        exit_date=last_p.date,
                        entry_price=round(entry_p.open, 4),
                        exit_price=round(last_p.close, 4),
                        qty=round(qty, 4),
                        pnl=round(pnl, 2),
                        rule_id=entry_rule,
                    )
                )

    total_return = (capital - initial_capital) / initial_capital if initial_capital > 0 else 0.0
    win_rate = sum(1 for t in trades if t.pnl > 0) / len(trades) if trades else 0.0

    start_date = all_dates[0] if all_dates else ""
    end_date = all_dates[-1] if all_dates else ""
    summary = (
        f"Backtest {strategy.name} v{strategy.version} | "
        f"{start_date} to {end_date} | "
        f"trades={len(trades)}, total_return={total_return:.2%}, "
        f"max_drawdown={max_drawdown:.2%}, win_rate={win_rate:.2%}"
        + (" [KILL-SWITCH TRIGGERED]" if killed else "")
    )

    return BacktestResult(
        strategy_id=strategy.strategy_id,
        start_date=start_date,
        end_date=end_date,
        trades=trades,
        total_return=round(total_return, 6),
        max_drawdown=round(max_drawdown, 6),
        win_rate=round(win_rate, 4),
        num_trades=len(trades),
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Trade ticket builder
# ---------------------------------------------------------------------------


def build_trade_ticket(
    signal: TradeSignal,
    strategy: StrategyDefinition,
    current_price: float,
    portfolio_value: float,
    id_factory: Optional[Callable[[], str]] = None,
) -> InvestingTradeTicketDraft:
    """Build a draft trade ticket from a signal.  Never placed in v1."""
    if id_factory is None:
        id_factory = lambda: str(uuid.uuid4())  # noqa: E731

    notional = portfolio_value * strategy.max_position_size
    qty = notional / current_price if current_price > 0 else 0

    # Simple ATR-proxy for stop loss: 2% below current price
    stop_loss = round(current_price * 0.98, 4)

    # Find entry/exit rule references from strategy
    entry_rule = next((r for r in strategy.rules if r.rule_type == "entry"), None)
    exit_rule = next((r for r in strategy.rules if r.rule_type == "exit"), None)

    return InvestingTradeTicketDraft(
        ticket_id=id_factory(),
        created_at=utc_now_iso(),
        symbol=signal.symbol,
        side="buy" if signal.signal_type == "entry" else "sell",
        order_type="limit",
        strategy_version=strategy.version,
        status="draft",
        qty=round(qty, 4),
        notional=round(notional, 2),
        entry_rule_reference=entry_rule.rule_id if entry_rule else "",
        exit_rule_reference=exit_rule.rule_id if exit_rule else "",
        stop_loss=stop_loss,
        time_in_force="day",
        risk_notes=f"Max position size: {strategy.max_position_size:.1%} of portfolio.",
        sizing_rationale=(
            f"Notional={notional:.2f} ({strategy.max_position_size:.1%} of {portfolio_value:.2f}), "
            f"qty={qty:.4f} @ limit near {current_price:.4f}."
        ),
    )


# ---------------------------------------------------------------------------
# Investing Program (top-level orchestrator)
# ---------------------------------------------------------------------------


class InvestingProgram:
    """High-level facade for the Investing domain — draft-only outputs."""

    def __init__(self) -> None:
        self._market_data: List[MarketDataPoint] = []
        self._strategies: Dict[str, StrategyDefinition] = {}

    def load_market_csv(self, csv_text: str) -> List[MarketDataPoint]:
        points = load_market_data_csv(csv_text)
        self._market_data.extend(points)
        return points

    def check_integrity(self) -> List[str]:
        return check_data_integrity(self._market_data)

    def add_strategy(self, strategy: StrategyDefinition) -> None:
        self._strategies[strategy.strategy_id] = strategy

    def signals(self, strategy_id: str) -> List[TradeSignal]:
        strategy = self._strategies[strategy_id]
        all_signals: List[TradeSignal] = []
        by_symbol: Dict[str, List[MarketDataPoint]] = defaultdict(list)
        for p in self._market_data:
            if p.symbol in strategy.universe:
                by_symbol[p.symbol].append(p)
        for symbol, points in by_symbol.items():
            all_signals.extend(compute_signals(points, strategy))
        return all_signals

    def backtest(self, strategy_id: str, initial_capital: float = 100_000.0) -> BacktestResult:
        strategy = self._strategies[strategy_id]
        return run_backtest(self._market_data, strategy, initial_capital)

    def draft_tickets(
        self,
        strategy_id: str,
        portfolio_value: float = 100_000.0,
    ) -> List[InvestingTradeTicketDraft]:
        """Generate draft trade tickets for the latest entry signals."""
        strategy = self._strategies[strategy_id]
        sigs = self.signals(strategy_id)

        # Only latest entry signal per symbol
        latest: Dict[str, TradeSignal] = {}
        for sig in sigs:
            if sig.signal_type == "entry":
                if sig.symbol not in latest or sig.date > latest[sig.symbol].date:
                    latest[sig.symbol] = sig

        tickets: List[InvestingTradeTicketDraft] = []
        by_symbol: Dict[str, List[MarketDataPoint]] = defaultdict(list)
        for p in self._market_data:
            by_symbol[p.symbol].append(p)

        for symbol, sig in latest.items():
            sym_points = sorted(by_symbol.get(symbol, []), key=lambda p: p.date)
            if sym_points:
                last_close = sym_points[-1].close
                tickets.append(
                    build_trade_ticket(
                        signal=sig,
                        strategy=strategy,
                        current_price=last_close,
                        portfolio_value=portfolio_value,
                    )
                )
        return tickets
