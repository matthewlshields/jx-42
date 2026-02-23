"""Tests for the Finance Program — Milestone 1."""
from __future__ import annotations

import unittest

from jx42.finance import (
    CsvImportError,
    FinanceProgram,
    build_debt_scenarios,
    detect_anomalies,
    estimate_runway,
    generate_monthly_report,
    generate_weekly_report,
    import_csv,
    reconcile,
)
from jx42.models import FinanceLedgerEntry

_SAMPLE_CSV = """\
date,amount,merchant,memo,account_id,currency
2026-01-05,-1200.00,Landlord,January rent,checking,USD
2026-01-06,-80.00,Con Edison,Electric bill,checking,USD
2026-01-10,5000.00,ACME Corp,Payroll direct deposit,checking,USD
2026-01-12,-50.00,Netflix,Monthly subscription,checking,USD
2026-01-15,-500.00,Kroger,Groceries,checking,USD
2026-01-20,-200.00,Amazon,Shopping,checking,USD
2026-01-22,-40.00,Spotify,Monthly subscription,checking,USD
2026-02-05,-1200.00,Landlord,February rent,checking,USD
2026-02-10,5000.00,ACME Corp,Payroll direct deposit,checking,USD
2026-02-15,-520.00,Kroger,Groceries,checking,USD
2026-02-20,-60.00,Netflix,Monthly subscription,checking,USD
2026-02-25,-45.00,Spotify,Monthly subscription,checking,USD
"""


class TestCsvImport(unittest.TestCase):
    def test_import_basic(self) -> None:
        entries = import_csv(_SAMPLE_CSV)
        self.assertEqual(12, len(entries))

    def test_categories_assigned(self) -> None:
        entries = import_csv(_SAMPLE_CSV)
        cats = {e.category for e in entries}
        self.assertIn("housing", cats)
        self.assertIn("salary", cats)
        self.assertIn("subscriptions", cats)
        self.assertIn("groceries", cats)

    def test_missing_amount_column(self) -> None:
        bad_csv = "date,merchant\n2026-01-01,Walmart"
        with self.assertRaises(CsvImportError):
            import_csv(bad_csv)

    def test_missing_date_column(self) -> None:
        bad_csv = "amount,merchant\n-50.00,Walmart"
        with self.assertRaises(CsvImportError):
            import_csv(bad_csv)

    def test_invalid_amount(self) -> None:
        bad_csv = "date,amount\n2026-01-01,notanumber"
        with self.assertRaises(CsvImportError):
            import_csv(bad_csv)


class TestReconciliation(unittest.TestCase):
    def _entries(self) -> list:
        return import_csv(_SAMPLE_CSV, account_id="checking")

    def test_reconcile_pass(self) -> None:
        entries = [e for e in self._entries() if e.account_id == "checking"]
        total = round(sum(e.amount for e in entries), 2)
        result = reconcile(entries, total)
        self.assertTrue(result.passed)
        self.assertAlmostEqual(0.0, result.delta, places=4)

    def test_reconcile_fail(self) -> None:
        entries = self._entries()
        result = reconcile(entries, 99999.00)
        self.assertFalse(result.passed)
        self.assertIn("FAILED", result.message)

    def test_reconcile_within_tolerance(self) -> None:
        entries = self._entries()
        total = round(sum(e.amount for e in entries), 2)
        result = reconcile(entries, total + 0.005, tolerance=0.01)
        self.assertTrue(result.passed)


class TestAnomalyDetection(unittest.TestCase):
    def test_no_anomalies_on_flat_data(self) -> None:
        entries = [
            FinanceLedgerEntry("1", "2026-01-01", -100.0, "USD", "a", category="groceries"),
            FinanceLedgerEntry("2", "2026-01-02", -100.0, "USD", "a", category="groceries"),
            FinanceLedgerEntry("3", "2026-01-03", -100.0, "USD", "a", category="groceries"),
        ]
        alerts = detect_anomalies(entries)
        self.assertEqual(0, len(alerts))

    def test_spike_detected(self) -> None:
        entries = [
            FinanceLedgerEntry("1", "2026-01-01", -100.0, "USD", "a", category="dining"),
            FinanceLedgerEntry("2", "2026-01-02", -105.0, "USD", "a", category="dining"),
            FinanceLedgerEntry("3", "2026-01-03", -98.0, "USD", "a", category="dining"),
            FinanceLedgerEntry("4", "2026-01-04", -102.0, "USD", "a", category="dining"),
            FinanceLedgerEntry("5", "2026-01-05", -1500.0, "USD", "a", category="dining"),  # large spike
        ]
        alerts = detect_anomalies(entries)
        spike_alerts = [a for a in alerts if a.reason == "spike"]
        self.assertGreater(len(spike_alerts), 0)

    def test_subscription_creep_detected(self) -> None:
        entries = import_csv(_SAMPLE_CSV)
        alerts = detect_anomalies(entries)
        creep_alerts = [a for a in alerts if a.reason == "subscription_creep"]
        self.assertGreater(len(creep_alerts), 0)


class TestRunwayEstimate(unittest.TestCase):
    def test_basic_runway(self) -> None:
        entries = import_csv(_SAMPLE_CSV)
        est = estimate_runway(entries, current_balance=20_000.0)
        self.assertGreater(est.months, 0)
        self.assertGreater(est.monthly_burn, 0)
        self.assertGreater(est.survival_budget, 0)

    def test_no_data(self) -> None:
        est = estimate_runway([], current_balance=10_000.0)
        self.assertEqual(0.0, est.months)


class TestDebtPayoff(unittest.TestCase):
    def test_avalanche(self) -> None:
        debts = [
            {"account_id": "card_a", "balance": 5000, "apr": 0.20, "min_payment": 100},
            {"account_id": "card_b", "balance": 2000, "apr": 0.15, "min_payment": 50},
        ]
        scenarios = build_debt_scenarios(debts, strategy="avalanche")
        self.assertEqual(2, len(scenarios))
        # Avalanche: highest APR (card_a) first
        self.assertEqual("card_a", scenarios[0].account_id)

    def test_snowball(self) -> None:
        debts = [
            {"account_id": "card_a", "balance": 5000, "apr": 0.20, "min_payment": 100},
            {"account_id": "card_b", "balance": 2000, "apr": 0.15, "min_payment": 50},
        ]
        scenarios = build_debt_scenarios(debts, strategy="snowball")
        # Snowball: lowest balance (card_b) first
        self.assertEqual("card_b", scenarios[0].account_id)

    def test_empty_debts(self) -> None:
        self.assertEqual([], build_debt_scenarios([]))


class TestMonthlyReport(unittest.TestCase):
    def test_monthly_totals(self) -> None:
        entries = import_csv(_SAMPLE_CSV)
        report = generate_monthly_report(entries, "2026-01")
        self.assertEqual("monthly", report.report_type)
        self.assertAlmostEqual(5000.0, report.total_income, places=2)
        # expenses: 1200+80+50+500+200+40 = 2070
        self.assertAlmostEqual(2070.0, report.total_expenses, places=2)
        self.assertAlmostEqual(5000.0 - 2070.0, report.net, places=2)

    def test_empty_month(self) -> None:
        entries = import_csv(_SAMPLE_CSV)
        report = generate_monthly_report(entries, "2025-12")
        self.assertEqual(0.0, report.total_income)
        self.assertEqual(0.0, report.total_expenses)


class TestWeeklyReport(unittest.TestCase):
    def test_weekly_net(self) -> None:
        entries = import_csv(_SAMPLE_CSV)
        # ISO week for 2026-01-05 is week 2
        report = generate_weekly_report(entries, "2026-W02")
        self.assertEqual("weekly", report.report_type)
        self.assertIsNotNone(report.net)


class TestFinanceProgram(unittest.TestCase):
    def test_full_pipeline(self) -> None:
        fp = FinanceProgram()
        entries = fp.import_csv(_SAMPLE_CSV, account_id="checking")
        self.assertEqual(12, len(entries))
        self.assertEqual(12, len(fp.ledger))

        report = fp.monthly_report("2026-01")
        self.assertEqual("monthly", report.report_type)

        recon = fp.reconcile("checking", statement_total=fp.monthly_report("2026-01").net)
        # reconcile against net is just a usage test — pass/fail depends on data
        self.assertIsNotNone(recon)

        est = fp.runway(20_000.0)
        self.assertGreater(est.months, 0)

        alerts = fp.anomalies()
        self.assertIsInstance(alerts, list)


if __name__ == "__main__":
    unittest.main()
