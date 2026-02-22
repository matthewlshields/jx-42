"""Finance Program — Milestone 1.

Responsibilities
----------------
- CSV import pipeline: parse rows into FinanceLedgerEntry objects.
- Normalisation + simple rule-based categorisation.
- Reconciliation: verify statement totals match ledger totals within tolerance.
- Reports: weekly delta, monthly close, runway/survival budget, debt payoff, anomalies.

All outputs are *draft-only*; no account changes are ever made here.
"""
from __future__ import annotations

import csv
import io
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from .models import (
    AnomalyAlert,
    DebtPayoffScenario,
    FinanceLedgerEntry,
    FinanceReport,
    RunwayEstimate,
)

# ---------------------------------------------------------------------------
# Category rules — simple keyword-based matching
# ---------------------------------------------------------------------------

_CATEGORY_RULES: List[Tuple[str, List[str]]] = [
    ("salary", ["payroll", "salary", "direct deposit", "ach deposit"]),
    ("housing", ["rent", "mortgage", "hoa"]),
    ("utilities", ["electric", "gas", "water", "internet", "cable", "phone"]),
    ("groceries", ["grocery", "supermarket", "whole foods", "trader joe", "safeway", "kroger"]),
    ("dining", ["restaurant", "cafe", "coffee", "starbucks", "mcdonald", "chipotle", "pizza"]),
    ("transport", ["uber", "lyft", "transit", "mta", "gas station", "fuel", "parking"]),
    ("healthcare", ["pharmacy", "cvs", "walgreen", "doctor", "dental", "vision", "hospital"]),
    ("subscriptions", ["netflix", "spotify", "hulu", "amazon prime", "apple", "google"]),
    ("insurance", ["insurance", "geico", "allstate", "progressive"]),
    ("debt_payment", ["loan", "credit card payment", "student loan"]),
    ("savings", ["savings transfer", "investment transfer", "brokerage"]),
    ("shopping", ["amazon", "target", "walmart", "ebay", "etsy"]),
]


def _categorize(merchant: str, memo: str) -> Tuple[str, float]:
    """Return (category, confidence) using keyword matching."""
    text = f"{merchant} {memo}".lower()
    for category, keywords in _CATEGORY_RULES:
        for kw in keywords:
            if kw in text:
                return category, 0.9
    return "uncategorized", 0.0


# ---------------------------------------------------------------------------
# CSV Importer
# ---------------------------------------------------------------------------

_REQUIRED_COLUMNS = {"date", "amount", "account_id"}


class CsvImportError(ValueError):
    pass


def import_csv(
    csv_text: str,
    account_id: str = "default",
    source: str = "bank_export",
    batch_id: Optional[str] = None,
    id_factory: Optional[Callable[[], str]] = None,
) -> List[FinanceLedgerEntry]:
    """Parse a CSV string into a list of FinanceLedgerEntry objects.

    Expected columns (case-insensitive): date, amount, [merchant | description], [memo], [currency]
    """
    if id_factory is None:
        def id_factory() -> str:
            return str(uuid.uuid4())
    if batch_id is None:
        batch_id = str(uuid.uuid4())

    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        raise CsvImportError("CSV has no headers.")

    headers = {h.strip().lower() for h in reader.fieldnames}
    if "amount" not in headers:
        raise CsvImportError("CSV must have an 'amount' column.")
    if "date" not in headers:
        raise CsvImportError("CSV must have a 'date' column.")

    entries: List[FinanceLedgerEntry] = []
    for i, row in enumerate(reader):
        row_lower = {k.strip().lower(): v.strip() for k, v in row.items()}
        try:
            amount = float(row_lower.get("amount", "0").replace(",", ""))
        except ValueError as exc:
            raise CsvImportError(f"Row {i + 1}: invalid amount '{row_lower.get('amount')}'") from exc

        raw_date = row_lower.get("date", "")
        merchant = row_lower.get("merchant", row_lower.get("description", row_lower.get("payee", "")))
        memo = row_lower.get("memo", row_lower.get("notes", ""))
        currency = row_lower.get("currency", "USD")
        acct = row_lower.get("account_id", account_id)

        category, confidence = _categorize(merchant, memo)

        entries.append(
            FinanceLedgerEntry(
                entry_id=id_factory(),
                date=raw_date,
                amount=amount,
                currency=currency,
                account_id=acct,
                merchant=merchant,
                category=category,
                category_confidence=confidence,
                memo=memo,
                source=source,
                import_batch_id=batch_id,
            )
        )
    return entries


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReconciliationResult:
    passed: bool
    ledger_total: float
    statement_total: float
    delta: float
    tolerance: float
    message: str


def reconcile(
    entries: Sequence[FinanceLedgerEntry],
    statement_total: float,
    tolerance: float = 0.01,
) -> ReconciliationResult:
    """Check that sum of ledger amounts matches statement_total within tolerance."""
    ledger_total = round(sum(e.amount for e in entries), 2)
    delta = abs(ledger_total - statement_total)
    passed = delta <= tolerance
    if passed:
        message = (
            f"Reconciliation passed: ledger={ledger_total:.2f}, "
            f"statement={statement_total:.2f}, delta={delta:.4f}"
        )
    else:
        message = (
            f"Reconciliation FAILED: ledger={ledger_total:.2f}, "
            f"statement={statement_total:.2f}, delta={delta:.4f} > tolerance={tolerance}"
        )
    return ReconciliationResult(
        passed=passed,
        ledger_total=ledger_total,
        statement_total=statement_total,
        delta=delta,
        tolerance=tolerance,
        message=message,
    )


# ---------------------------------------------------------------------------
# Anomaly Detection
# ---------------------------------------------------------------------------

_SPIKE_STD_MULTIPLIER = 2.0  # flag if > 2 std devs above category mean


def detect_anomalies(entries: Sequence[FinanceLedgerEntry]) -> List[AnomalyAlert]:
    """Flag spend spikes and subscription creep."""
    alerts: List[AnomalyAlert] = []

    # Group expenses by category
    by_category: Dict[str, List[FinanceLedgerEntry]] = defaultdict(list)
    for e in entries:
        if e.amount < 0:
            by_category[e.category].append(e)

    for category, cat_entries in by_category.items():
        if len(cat_entries) < 2:
            continue
        amounts = [abs(e.amount) for e in cat_entries]
        for i, entry in enumerate(cat_entries):
            # Compute mean/std from all other entries (leave-one-out) to avoid
            # the outlier inflating the threshold
            others = [a for j, a in enumerate(amounts) if j != i]
            if not others:
                continue
            mean = sum(others) / len(others)
            variance = sum((a - mean) ** 2 for a in others) / len(others)
            std = variance ** 0.5
            threshold = mean + _SPIKE_STD_MULTIPLIER * std
            if abs(entry.amount) > threshold and std > 0:
                alerts.append(
                    AnomalyAlert(
                        entry_id=entry.entry_id,
                        date=entry.date,
                        amount=entry.amount,
                        category=category,
                        reason="spike",
                    )
                )

    # Subscription creep: flag categories whose total grows month-over-month
    monthly: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for e in entries:
        if e.category == "subscriptions" and e.amount < 0:
            month = e.date[:7]  # YYYY-MM
            monthly[month]["subscriptions"] += abs(e.amount)

    months = sorted(monthly.keys())
    for i in range(1, len(months)):
        prev = monthly[months[i - 1]].get("subscriptions", 0.0)
        curr = monthly[months[i]].get("subscriptions", 0.0)
        if prev > 0 and curr > prev * 1.1:
            alerts.append(
                AnomalyAlert(
                    entry_id="",
                    date=months[i],
                    amount=curr - prev,
                    category="subscriptions",
                    reason="subscription_creep",
                )
            )

    return alerts


# ---------------------------------------------------------------------------
# Runway & Survival Budget
# ---------------------------------------------------------------------------


def estimate_runway(
    entries: Sequence[FinanceLedgerEntry],
    current_balance: float,
    essential_categories: Optional[List[str]] = None,
) -> RunwayEstimate:
    """Estimate months of runway given current balance and average monthly burn."""
    if essential_categories is None:
        essential_categories = ["housing", "utilities", "groceries", "healthcare", "insurance"]

    # Calculate average monthly burn (expenses only) over available months
    monthly_expenses: Dict[str, float] = defaultdict(float)
    for e in entries:
        if e.amount < 0:
            monthly_expenses[e.date[:7]] += abs(e.amount)

    if not monthly_expenses:
        return RunwayEstimate(
            months=0.0,
            monthly_burn=0.0,
            current_balance=current_balance,
            survival_budget=0.0,
            assumptions="No expense data available.",
        )

    avg_burn = sum(monthly_expenses.values()) / len(monthly_expenses)

    # Survival budget = only essential categories
    monthly_essential: Dict[str, float] = defaultdict(float)
    for e in entries:
        if e.amount < 0 and e.category in essential_categories:
            monthly_essential[e.date[:7]] += abs(e.amount)

    survival_budget = (
        sum(monthly_essential.values()) / len(monthly_essential) if monthly_essential else avg_burn * 0.6
    )

    months = current_balance / avg_burn if avg_burn > 0 else float("inf")

    return RunwayEstimate(
        months=round(months, 1),
        monthly_burn=round(avg_burn, 2),
        current_balance=current_balance,
        survival_budget=round(survival_budget, 2),
        assumptions=(
            f"Based on {len(monthly_expenses)} months of data. "
            f"Survival budget includes: {', '.join(essential_categories)}."
        ),
    )


# ---------------------------------------------------------------------------
# Debt Payoff Scenarios
# ---------------------------------------------------------------------------


def build_debt_scenarios(
    debts: List[Dict[str, Any]],
    extra_monthly: float = 0.0,
    strategy: str = "avalanche",
) -> List[DebtPayoffScenario]:
    """Draft debt payoff scenarios using avalanche (highest APR first) or snowball (lowest balance first).

    Each debt dict: {account_id, balance, apr, min_payment}
    """
    if not debts:
        return []

    # Sort by strategy
    if strategy == "avalanche":
        sorted_debts = sorted(debts, key=lambda d: d.get("apr", 0), reverse=True)
    else:
        sorted_debts = sorted(debts, key=lambda d: d.get("balance", 0))

    scenarios: List[DebtPayoffScenario] = []
    remaining_extra = extra_monthly

    for debt in sorted_debts:
        balance = float(debt.get("balance", 0))
        apr = float(debt.get("apr", 0.20))
        min_payment = float(debt.get("min_payment", balance * 0.02))
        acct = str(debt.get("account_id", "unknown"))

        payment = min_payment + remaining_extra
        monthly_rate = apr / 12.0

        if monthly_rate == 0:
            months = balance / payment if payment > 0 else float("inf")
            total_interest = 0.0
        else:
            if payment <= balance * monthly_rate:
                months = float("inf")
                total_interest = float("inf")
            else:
                import math

                months = -math.log(1 - (balance * monthly_rate) / payment) / math.log(1 + monthly_rate)
                total_interest = round(payment * months - balance, 2)

        scenarios.append(
            DebtPayoffScenario(
                account_id=acct,
                balance=round(balance, 2),
                monthly_payment=round(payment, 2),
                months_to_payoff=round(months, 1),
                total_interest=total_interest,
                strategy=strategy,
            )
        )
        # In avalanche/snowball, once first debt is paid off, roll payment to next
        remaining_extra = 0.0  # simplified: only apply extra to first

    return scenarios


# ---------------------------------------------------------------------------
# Finance Reporter
# ---------------------------------------------------------------------------


def generate_monthly_report(entries: Sequence[FinanceLedgerEntry], month: str) -> FinanceReport:
    """Generate a monthly close report for the given YYYY-MM period."""
    period_entries = [e for e in entries if e.date.startswith(month)]

    income = sum(e.amount for e in period_entries if e.amount > 0)
    expenses = sum(abs(e.amount) for e in period_entries if e.amount < 0)
    net = income - expenses

    by_cat: Dict[str, float] = defaultdict(float)
    for e in period_entries:
        if e.amount < 0:
            by_cat[e.category] += abs(e.amount)
    top_cats = sorted(
        [{"category": k, "total": round(v, 2)} for k, v in by_cat.items()],
        key=lambda x: x["total"],
        reverse=True,
    )[:5]

    anomalies = detect_anomalies(period_entries)

    summary = (
        f"Monthly close {month}: income={income:.2f}, expenses={expenses:.2f}, net={net:.2f}. "
        f"Top category: {top_cats[0]['category'] if top_cats else 'none'}."
    )

    return FinanceReport(
        period=month,
        report_type="monthly",
        total_income=round(income, 2),
        total_expenses=round(expenses, 2),
        net=round(net, 2),
        top_categories=top_cats,
        anomalies=anomalies,
        runway=None,
        debt_scenarios=[],
        summary=summary,
    )


def generate_weekly_report(entries: Sequence[FinanceLedgerEntry], year_week: str) -> FinanceReport:
    """Generate a weekly delta report for the given ISO year-week (e.g. '2026-W03')."""
    year_str, week_str = year_week.split("-W")
    year, week = int(year_str), int(week_str)

    def _iso_week(d_str: str) -> Tuple[int, int]:
        try:
            d = date.fromisoformat(d_str)
            iso = d.isocalendar()
            return iso.year, iso.week
        except ValueError:
            return 0, 0

    period_entries = [e for e in entries if _iso_week(e.date) == (year, week)]

    income = sum(e.amount for e in period_entries if e.amount > 0)
    expenses = sum(abs(e.amount) for e in period_entries if e.amount < 0)
    net = income - expenses

    by_cat: Dict[str, float] = defaultdict(float)
    for e in period_entries:
        if e.amount < 0:
            by_cat[e.category] += abs(e.amount)
    top_cats = sorted(
        [{"category": k, "total": round(v, 2)} for k, v in by_cat.items()],
        key=lambda x: x["total"],
        reverse=True,
    )[:5]

    summary = f"Weekly delta {year_week}: income={income:.2f}, expenses={expenses:.2f}, net={net:.2f}."

    return FinanceReport(
        period=year_week,
        report_type="weekly",
        total_income=round(income, 2),
        total_expenses=round(expenses, 2),
        net=round(net, 2),
        top_categories=top_cats,
        anomalies=[],
        runway=None,
        debt_scenarios=[],
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Finance Program (top-level orchestrator)
# ---------------------------------------------------------------------------


class FinanceProgram:
    """High-level facade for the Finance domain — draft-only outputs."""

    def __init__(self, ledger: Optional[List[FinanceLedgerEntry]] = None) -> None:
        self._ledger: List[FinanceLedgerEntry] = list(ledger) if ledger else []

    @property
    def ledger(self) -> List[FinanceLedgerEntry]:
        return list(self._ledger)

    def import_csv(
        self,
        csv_text: str,
        account_id: str = "default",
        source: str = "bank_export",
        batch_id: Optional[str] = None,
    ) -> List[FinanceLedgerEntry]:
        entries = import_csv(csv_text, account_id=account_id, source=source, batch_id=batch_id)
        self._ledger.extend(entries)
        return entries

    def reconcile(self, account_id: str, statement_total: float, tolerance: float = 0.01) -> ReconciliationResult:
        subset = [e for e in self._ledger if e.account_id == account_id]
        return reconcile(subset, statement_total, tolerance)

    def monthly_report(self, month: str) -> FinanceReport:
        return generate_monthly_report(self._ledger, month)

    def weekly_report(self, year_week: str) -> FinanceReport:
        return generate_weekly_report(self._ledger, year_week)

    def runway(self, current_balance: float, essential_categories: Optional[List[str]] = None) -> RunwayEstimate:
        return estimate_runway(self._ledger, current_balance, essential_categories)

    def debt_payoff(
        self,
        debts: List[Dict[str, Any]],
        extra_monthly: float = 0.0,
        strategy: str = "avalanche",
    ) -> List[DebtPayoffScenario]:
        return build_debt_scenarios(debts, extra_monthly, strategy)

    def anomalies(self) -> List[AnomalyAlert]:
        return detect_anomalies(self._ledger)
