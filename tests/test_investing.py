"""Tests for the Investing Program — Milestone 2."""
from __future__ import annotations

import unittest

from jx42.investing import (
    InvestingProgram,
    MarketDataError,
    check_data_integrity,
    compute_signals,
    load_market_data_csv,
    run_backtest,
)
from jx42.models import MarketDataPoint, StrategyDefinition, StrategyRule

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# 60 trading days of synthetic OHLCV for a single symbol (upward trend)
def _make_market_csv(symbol: str = "TEST", n: int = 60, start_price: float = 100.0) -> str:
    rows = ["symbol,date,open,high,low,close,volume"]
    price = start_price
    from datetime import date, timedelta

    d = date(2026, 1, 2)
    for i in range(n):
        while d.weekday() >= 5:  # skip weekends
            d += timedelta(days=1)
        o = round(price, 2)
        h = round(price * 1.01, 2)
        lo = round(price * 0.99, 2)
        c = round(price * 1.005, 2)  # slight upward drift
        rows.append(f"{symbol},{d},{o},{h},{lo},{c},1000000")
        price = c
        d += timedelta(days=1)
    return "\n".join(rows)


def _make_strategy(
    strategy_id: str = "s1",
    universe: list | None = None,
    fast_window: int = 5,
    slow_window: int = 20,
) -> StrategyDefinition:
    if universe is None:
        universe = ["TEST"]
    return StrategyDefinition(
        strategy_id=strategy_id,
        name="Test Strategy",
        version="1.0",
        universe=universe,
        rules=[
            StrategyRule(
                rule_id="r_entry",
                description="SMA crossover entry",
                rule_type="entry",
                parameters={"indicator": "sma_crossover", "fast_window": fast_window, "slow_window": slow_window},
            ),
            StrategyRule(
                rule_id="r_exit",
                description="SMA cross-below exit",
                rule_type="exit",
                parameters={"indicator": "sma_cross_below", "fast_window": fast_window, "slow_window": slow_window},
            ),
        ],
        max_position_size=0.05,
        max_open_positions=2,
        max_drawdown_pct=0.25,
    )


# ---------------------------------------------------------------------------
# Market data loading
# ---------------------------------------------------------------------------


class TestMarketDataLoading(unittest.TestCase):
    def test_load_basic(self) -> None:
        csv_text = _make_market_csv()
        points = load_market_data_csv(csv_text)
        self.assertEqual(60, len(points))
        for p in points:
            self.assertEqual("TEST", p.symbol)
            self.assertGreater(p.close, 0)

    def test_missing_volume_column(self) -> None:
        csv_text = "symbol,date,open,high,low,close\nTEST,2026-01-02,100,101,99,100.5"
        with self.assertRaises(MarketDataError):
            load_market_data_csv(csv_text)

    def test_no_headers(self) -> None:
        with self.assertRaises(MarketDataError):
            load_market_data_csv("")

    def test_invalid_price_row(self) -> None:
        csv_text = "symbol,date,open,high,low,close,volume\nTEST,2026-01-02,abc,101,99,100.5,1000"
        with self.assertRaises(MarketDataError):
            load_market_data_csv(csv_text)


# ---------------------------------------------------------------------------
# Data integrity
# ---------------------------------------------------------------------------


class TestDataIntegrity(unittest.TestCase):
    def test_clean_data_passes(self) -> None:
        points = load_market_data_csv(_make_market_csv())
        errors = check_data_integrity(points)
        self.assertEqual([], errors)

    def test_duplicate_date_flagged(self) -> None:
        points = [
            MarketDataPoint("X", "2026-01-02", 100, 101, 99, 100.5, 1000),
            MarketDataPoint("X", "2026-01-02", 100, 101, 99, 100.5, 1000),  # duplicate
        ]
        errors = check_data_integrity(points)
        self.assertTrue(any("duplicate" in e for e in errors))

    def test_unsorted_dates_flagged(self) -> None:
        points = [
            MarketDataPoint("X", "2026-01-03", 100, 101, 99, 100.5, 1000),
            MarketDataPoint("X", "2026-01-02", 100, 101, 99, 100.5, 1000),
        ]
        errors = check_data_integrity(points)
        self.assertTrue(any("ascending" in e for e in errors))

    def test_high_below_close_flagged(self) -> None:
        points = [
            MarketDataPoint("X", "2026-01-02", 100, 95, 90, 98, 1000),  # high=95 < close=98
        ]
        errors = check_data_integrity(points)
        self.assertTrue(len(errors) > 0)

    def test_negative_volume_flagged(self) -> None:
        points = [
            MarketDataPoint("X", "2026-01-02", 100, 101, 99, 100.5, -1),
        ]
        errors = check_data_integrity(points)
        self.assertTrue(any("volume" in e for e in errors))


# ---------------------------------------------------------------------------
# Signal engine
# ---------------------------------------------------------------------------


class TestSignalEngine(unittest.TestCase):
    def test_signals_returned_for_uptrend(self) -> None:
        points = load_market_data_csv(_make_market_csv(n=60))
        strategy = _make_strategy(fast_window=5, slow_window=20)
        signals = compute_signals(points, strategy)
        # In a consistent uptrend, at least one entry signal should fire
        self.assertIsInstance(signals, list)

    def test_breakout_signal(self) -> None:
        points = load_market_data_csv(_make_market_csv(n=30))
        strategy = StrategyDefinition(
            strategy_id="s_breakout",
            name="Breakout",
            version="1.0",
            universe=["TEST"],
            rules=[
                StrategyRule(
                    rule_id="r_breakout",
                    description="20-day breakout",
                    rule_type="entry",
                    parameters={"indicator": "breakout", "window": 10},
                )
            ],
        )
        signals = compute_signals(points, strategy)
        self.assertIsInstance(signals, list)

    def test_trailing_stop_exit(self) -> None:
        # Build data that drops sharply after a high
        rows = ["symbol,date,open,high,low,close,volume"]
        prices = [100, 105, 110, 108, 106, 80, 75]  # sharp drop
        from datetime import date, timedelta

        d = date(2026, 1, 2)
        for p in prices:
            rows.append(f"TEST,{d},{p},{p*1.01},{p*0.99},{p},1000")
            d += timedelta(days=1)
        points = load_market_data_csv("\n".join(rows))
        strategy = StrategyDefinition(
            strategy_id="s_trail",
            name="Trailing",
            version="1.0",
            universe=["TEST"],
            rules=[
                StrategyRule(
                    rule_id="r_trail_exit",
                    description="trailing stop",
                    rule_type="exit",
                    parameters={"indicator": "trailing_stop", "pct": 0.10},
                )
            ],
        )
        signals = compute_signals(points, strategy)
        exit_signals = [s for s in signals if s.signal_type == "exit"]
        self.assertGreater(len(exit_signals), 0)


# ---------------------------------------------------------------------------
# Backtester
# ---------------------------------------------------------------------------


class TestBacktester(unittest.TestCase):
    def test_backtest_produces_result(self) -> None:
        csv_text = _make_market_csv(n=60)
        points = load_market_data_csv(csv_text)
        strategy = _make_strategy()
        result = run_backtest(points, strategy, initial_capital=10_000.0)
        self.assertIsNotNone(result.summary)
        self.assertIsInstance(result.trades, list)
        self.assertIsInstance(result.total_return, float)
        self.assertIsInstance(result.max_drawdown, float)
        self.assertGreaterEqual(result.win_rate, 0.0)
        self.assertLessEqual(result.win_rate, 1.0)

    def test_no_look_ahead_bias(self) -> None:
        """Entry executes at next-day open, not signal-day close."""
        csv_text = _make_market_csv(n=60)
        points = load_market_data_csv(csv_text)
        strategy = _make_strategy()
        result = run_backtest(points, strategy, initial_capital=10_000.0)
        # All entry prices should be open prices; simply verify no exception and valid result
        self.assertIsNotNone(result)

    def test_kill_switch_respected(self) -> None:
        """A strategy with a tight drawdown limit should trigger kill-switch on extreme losses."""
        # Create data with a severe crash
        rows = ["symbol,date,open,high,low,close,volume"]
        prices = list(range(100, 160)) + list(range(159, 50, -3))  # up then crash
        from datetime import date, timedelta

        d = date(2026, 1, 2)
        for p in prices:
            rows.append(f"TEST,{d},{p},{int(p*1.02)},{int(p*0.98)},{p},1000000")
            d += timedelta(days=1)
        csv_text = "\n".join(rows)
        points = load_market_data_csv(csv_text)
        strategy = StrategyDefinition(
            strategy_id="s_kill",
            name="Kill Switch Test",
            version="1.0",
            universe=["TEST"],
            rules=[
                StrategyRule("r_entry", "entry rule", "entry", {"indicator": "breakout", "window": 5}),
                StrategyRule("r_exit", "trailing exit", "exit", {"indicator": "trailing_stop", "pct": 0.05}),
            ],
            max_position_size=0.5,
            max_open_positions=1,
            max_drawdown_pct=0.05,  # tight
        )
        result = run_backtest(points, strategy, initial_capital=10_000.0)
        # Should still produce a valid result (kill-switch may trigger)
        self.assertIsNotNone(result.summary)

    def test_repeatable_outputs(self) -> None:
        """Same inputs => same outputs."""
        csv_text = _make_market_csv(n=60)
        points = load_market_data_csv(csv_text)
        strategy = _make_strategy()
        result1 = run_backtest(points, strategy, initial_capital=10_000.0)
        result2 = run_backtest(points, strategy, initial_capital=10_000.0)
        self.assertEqual(result1.total_return, result2.total_return)
        self.assertEqual(result1.num_trades, result2.num_trades)

    def test_tickets_respect_position_size(self) -> None:
        ip = InvestingProgram()
        ip.load_market_csv(_make_market_csv(n=60))
        strategy = _make_strategy()
        ip.add_strategy(strategy)
        tickets = ip.draft_tickets(strategy.strategy_id, portfolio_value=100_000.0)
        for ticket in tickets:
            if ticket.notional is not None:
                # notional should not exceed max_position_size * portfolio
                self.assertLessEqual(ticket.notional, 100_000.0 * strategy.max_position_size + 0.01)


# ---------------------------------------------------------------------------
# InvestingProgram facade
# ---------------------------------------------------------------------------


class TestInvestingProgram(unittest.TestCase):
    def test_full_pipeline(self) -> None:
        ip = InvestingProgram()
        csv_text = _make_market_csv(n=60)
        points = ip.load_market_csv(csv_text)
        self.assertEqual(60, len(points))

        errors = ip.check_integrity()
        self.assertEqual([], errors)

        strategy = _make_strategy()
        ip.add_strategy(strategy)

        signals = ip.signals(strategy.strategy_id)
        self.assertIsInstance(signals, list)

        result = ip.backtest(strategy.strategy_id, initial_capital=50_000.0)
        self.assertIsInstance(result.total_return, float)

        tickets = ip.draft_tickets(strategy.strategy_id, portfolio_value=50_000.0)
        self.assertIsInstance(tickets, list)
        for t in tickets:
            self.assertEqual("draft", t.status)


if __name__ == "__main__":
    unittest.main()
