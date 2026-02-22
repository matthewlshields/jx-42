from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .audit import InMemoryAuditLog
from .finance import FinanceProgram
from .investing import InvestingProgram
from .kernel import DefaultKernel, KernelConfig
from .memory import InMemoryMemoryLibrarian
from .models import StrategyDefinition, StrategyRule, UserRequest
from .policy import DefaultPolicyGuardian
from .storage import (
    SqliteAuditLog,
    SqliteFinanceLedger,
    SqliteMarketDataStore,
    SqliteMemoryLibrarian,
)

_DEFAULT_DB = Path.home() / ".jx42" / "jx42.db"


def _ensure_db_dir(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jx-42", description="JX-42 CLI")
    parser.add_argument(
        "--db",
        default=str(_DEFAULT_DB),
        help=f"SQLite database path (default: {_DEFAULT_DB})",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ---- run (original kernel request) ----
    run_parser = subparsers.add_parser("run", help="Run a single request")
    run_parser.add_argument("text", help="Request text")
    run_parser.add_argument("--seed", type=int, default=None, help="Determinism seed")
    run_parser.add_argument("--no-persist", action="store_true", help="Use in-memory storage only")

    # ---- finance sub-commands ----
    finance_parser = subparsers.add_parser("finance", help="Finance program commands")
    finance_sub = finance_parser.add_subparsers(dest="finance_command", required=True)

    import_parser = finance_sub.add_parser("import-csv", help="Import a CSV bank export into the ledger")
    import_parser.add_argument("file", help="Path to CSV file")
    import_parser.add_argument("--account-id", default="default", help="Account identifier")
    import_parser.add_argument("--source", default="bank_export", choices=["bank_export", "manual"])

    report_parser = finance_sub.add_parser("report", help="Generate a monthly or weekly report")
    report_parser.add_argument("period", help="Period in YYYY-MM (monthly) or YYYY-Www (weekly) format")

    reconcile_parser = finance_sub.add_parser("reconcile", help="Reconcile ledger against statement total")
    reconcile_parser.add_argument("account_id", help="Account ID to reconcile")
    reconcile_parser.add_argument("statement_total", type=float, help="Statement total (positive = net credit)")

    runway_parser = finance_sub.add_parser("runway", help="Estimate financial runway")
    runway_parser.add_argument("balance", type=float, help="Current liquid balance")

    debt_parser = finance_sub.add_parser("debt-payoff", help="Draft debt payoff scenarios")
    debt_parser.add_argument("debts_json", help="JSON array of debt objects: [{account_id, balance, apr, min_payment}]")
    debt_parser.add_argument("--extra", type=float, default=0.0, help="Extra monthly payment")
    debt_parser.add_argument("--strategy", default="avalanche", choices=["avalanche", "snowball"])

    finance_sub.add_parser("anomalies", help="Detect spending anomalies")

    # ---- investing sub-commands ----
    inv_parser = subparsers.add_parser("investing", help="Investing program commands")
    inv_sub = inv_parser.add_subparsers(dest="investing_command", required=True)

    inv_load = inv_sub.add_parser("load-market-data", help="Load OHLCV market data from CSV")
    inv_load.add_argument("file", help="Path to CSV file with symbol,date,open,high,low,close,volume columns")

    inv_sub.add_parser("check-data", help="Run data integrity checks on loaded market data")

    inv_signals = inv_sub.add_parser("signals", help="Compute trading signals for a strategy")
    inv_signals.add_argument("strategy_file", help="Path to JSON strategy definition file")

    inv_backtest = inv_sub.add_parser("backtest", help="Run backtest for a strategy")
    inv_backtest.add_argument("strategy_file", help="Path to JSON strategy definition file")
    inv_backtest.add_argument("--capital", type=float, default=100_000.0, help="Initial capital")

    inv_tickets = inv_sub.add_parser("draft-tickets", help="Generate draft trade tickets for latest signals")
    inv_tickets.add_argument("strategy_file", help="Path to JSON strategy definition file")
    inv_tickets.add_argument("--portfolio-value", type=float, default=100_000.0, help="Portfolio value")

    return parser


def _load_strategy(path: str) -> StrategyDefinition:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    rules = [
        StrategyRule(
            rule_id=r["rule_id"],
            description=r.get("description", ""),
            rule_type=r["rule_type"],
            parameters=r.get("parameters", {}),
        )
        for r in data.get("rules", [])
    ]
    return StrategyDefinition(
        strategy_id=data["strategy_id"],
        name=data["name"],
        version=data["version"],
        universe=data["universe"],
        rules=rules,
        max_position_size=float(data.get("max_position_size", 0.01)),
        max_open_positions=int(data.get("max_open_positions", 3)),
        max_drawdown_pct=float(data.get("max_drawdown_pct", 0.10)),
    )


def _build_audit_log(args: argparse.Namespace):
    if getattr(args, "no_persist", False):
        return InMemoryAuditLog()
    db_path = Path(args.db)
    _ensure_db_dir(db_path)
    return SqliteAuditLog(db_path)


def _build_memory(args: argparse.Namespace):
    if getattr(args, "no_persist", False):
        return InMemoryMemoryLibrarian()
    db_path = Path(args.db)
    _ensure_db_dir(db_path)
    return SqliteMemoryLibrarian(db_path)


def _backtest_json_default(o: object) -> object:
    """JSON serializer that falls back to __dict__ then str."""
    return o.__dict__ if hasattr(o, "__dict__") else str(o)


def _handle_run(args: argparse.Namespace) -> int:
    kernel = DefaultKernel(
        policy_guardian=DefaultPolicyGuardian(),
        memory_librarian=_build_memory(args),
        audit_log=_build_audit_log(args),
        config=KernelConfig(determinism_seed=args.seed),
    )
    try:
        response = kernel.handle_request(UserRequest(text=args.text))
        print(f"correlation_id={response.correlation_id}")
        print(response.response_text)
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _handle_finance(args: argparse.Namespace, db_path: Path) -> int:
    _ensure_db_dir(db_path)
    ledger_store = SqliteFinanceLedger(db_path)
    fp = FinanceProgram(ledger=ledger_store.load_all())

    if args.finance_command == "import-csv":
        try:
            csv_text = Path(args.file).read_text(encoding="utf-8")
            entries = fp.import_csv(csv_text, account_id=args.account_id, source=args.source)
            ledger_store.save(entries)
            print(f"Imported {len(entries)} entries into account '{args.account_id}'.")
            return 0
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    if args.finance_command == "report":
        period = args.period
        try:
            if "W" in period.upper():
                report = fp.weekly_report(period.upper().replace("w", "W"))
            else:
                report = fp.monthly_report(period)
            print(json.dumps(report.__dict__, default=str, indent=2))
            return 0
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    if args.finance_command == "reconcile":
        result = fp.reconcile(args.account_id, args.statement_total)
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.message}")
        return 0 if result.passed else 1

    if args.finance_command == "runway":
        est = fp.runway(args.balance)
        print(json.dumps(est.__dict__, default=str, indent=2))
        return 0

    if args.finance_command == "debt-payoff":
        try:
            debts = json.loads(args.debts_json)
        except json.JSONDecodeError as exc:
            print(f"error: invalid JSON for debts: {exc}", file=sys.stderr)
            return 1
        scenarios = fp.debt_payoff(debts, extra_monthly=args.extra, strategy=args.strategy)
        print(json.dumps([s.__dict__ for s in scenarios], default=str, indent=2))
        return 0

    if args.finance_command == "anomalies":
        alerts = fp.anomalies()
        print(json.dumps([a.__dict__ for a in alerts], default=str, indent=2))
        return 0

    return 1


def _handle_investing(args: argparse.Namespace, db_path: Path) -> int:
    _ensure_db_dir(db_path)
    market_store = SqliteMarketDataStore(db_path)
    ip = InvestingProgram()
    for p in market_store.load_all():
        ip._market_data.append(p)

    if args.investing_command == "load-market-data":
        try:
            csv_text = Path(args.file).read_text(encoding="utf-8")
            points = ip.load_market_csv(csv_text)
            market_store.save(points)
            print(f"Loaded {len(points)} market data points.")
            return 0
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    if args.investing_command == "check-data":
        errors = ip.check_integrity()
        if errors:
            for e in errors:
                print(f"  INTEGRITY ERROR: {e}")
            return 1
        print(f"Data integrity OK ({len(ip._market_data)} points).")
        return 0

    if args.investing_command in ("signals", "backtest", "draft-tickets"):
        try:
            strategy = _load_strategy(args.strategy_file)
        except Exception as exc:
            print(f"error: could not load strategy: {exc}", file=sys.stderr)
            return 1
        ip.add_strategy(strategy)

        if args.investing_command == "signals":
            sigs = ip.signals(strategy.strategy_id)
            print(json.dumps([s.__dict__ for s in sigs], default=str, indent=2))
            return 0

        if args.investing_command == "backtest":
            result = ip.backtest(strategy.strategy_id, initial_capital=args.capital)
            print(result.summary)
            print(json.dumps(result.__dict__, default=_backtest_json_default, indent=2))
            return 0

        if args.investing_command == "draft-tickets":
            tickets = ip.draft_tickets(strategy.strategy_id, portfolio_value=args.portfolio_value)
            print(json.dumps([t.to_dict() for t in tickets], default=str, indent=2))
            return 0

    return 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    db_path = Path(args.db)

    if args.command == "run":
        return _handle_run(args)

    if args.command == "finance":
        return _handle_finance(args, db_path)

    if args.command == "investing":
        return _handle_investing(args, db_path)

    return 1


if __name__ == "__main__":
    sys.exit(main())

