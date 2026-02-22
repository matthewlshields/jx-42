import unittest

from jx42.validation import validate_audit_event, validate_finance_ledger_entry, validate_investing_trade_ticket


class TestValidation(unittest.TestCase):
    def test_audit_event_valid(self) -> None:
        payload = {
            "event_id": "test-1",
            "timestamp": "2026-01-01T00:00:00+00:00",
            "correlation_id": "corr-1",
            "component": "kernel",
            "action_type": "plan_created",
            "risk_level": "low",
            "policy_decision": "allow",
        }
        errors = validate_audit_event(payload)
        self.assertEqual([], errors)

    def test_audit_event_missing_field(self) -> None:
        payload = {
            "event_id": "test-1",
            "timestamp": "2026-01-01T00:00:00+00:00",
        }
        errors = validate_audit_event(payload)
        self.assertIn("Missing required field: correlation_id", errors)

    def test_finance_entry_valid(self) -> None:
        payload = {
            "entry_id": "entry-1",
            "date": "2026-01-01",
            "amount": 100.0,
            "currency": "USD",
            "account_id": "checking",
            "source": "bank_export",
            "import_batch_id": "batch-1",
        }
        errors = validate_finance_ledger_entry(payload)
        self.assertEqual([], errors)

    def test_investing_trade_ticket_valid(self) -> None:
        payload = {
            "ticket_id": "ticket-1",
            "created_at": "2026-01-01T00:00:00+00:00",
            "symbol": "AAPL",
            "side": "buy",
            "order_type": "limit",
            "strategy_version": "v1",
            "status": "draft",
        }
        errors = validate_investing_trade_ticket(payload)
        self.assertEqual([], errors)

    def test_investing_trade_ticket_missing_field(self) -> None:
        payload = {"ticket_id": "ticket-1", "symbol": "AAPL"}
        errors = validate_investing_trade_ticket(payload)
        self.assertIn("Missing required field: created_at", errors)


if __name__ == "__main__":
    unittest.main()
