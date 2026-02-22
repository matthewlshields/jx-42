import unittest

from jx42.audit import InMemoryAuditLog, redact_text
from jx42.models import AuditEvent, PolicyDecisionType, RiskLevel


class TestAuditLog(unittest.TestCase):
    def test_append_only(self) -> None:
        log = InMemoryAuditLog()
        event1 = AuditEvent(
            event_id="event-1",
            timestamp="2026-01-01T00:00:00+00:00",
            correlation_id="corr-1",
            component="kernel",
            action_type="plan_created",
            risk_level=RiskLevel.LOW,
            inputs_summary="hello",
            outputs_summary="plan",
            policy_decision=PolicyDecisionType.ALLOW,
            rationale="ok",
        )
        event2 = AuditEvent(
            event_id="event-2",
            timestamp="2026-01-01T00:00:01+00:00",
            correlation_id="corr-1",
            component="kernel",
            action_type="response_generated",
            risk_level=RiskLevel.LOW,
            inputs_summary="hello",
            outputs_summary="response",
            policy_decision=PolicyDecisionType.ALLOW,
            rationale="ok",
        )
        log.append(event1)
        log.append(event2)
        events = log.list_events()
        self.assertEqual(2, len(events))
        self.assertEqual("event-1", events[0].event_id)
        self.assertEqual("event-2", events[1].event_id)

    def test_to_dict(self) -> None:
        event = AuditEvent(
            event_id="event-1",
            timestamp="2026-01-01T00:00:00+00:00",
            correlation_id="corr-1",
            component="kernel",
            action_type="plan_created",
            risk_level=RiskLevel.LOW,
            inputs_summary="hello",
            outputs_summary="plan",
            policy_decision=PolicyDecisionType.ALLOW,
            rationale="ok",
        )
        d = event.to_dict()
        self.assertEqual("event-1", d["event_id"])
        self.assertEqual("low", d["risk_level"])
        self.assertEqual("allow", d["policy_decision"])

    def test_redaction(self) -> None:
        text = "password=secret123 token:abcd sk-TESTTOKEN"
        redacted = redact_text(text)
        self.assertIn("password=[REDACTED]", redacted)
        self.assertIn("token:[REDACTED]", redacted)
        self.assertIn("[REDACTED]", redacted)


if __name__ == "__main__":
    unittest.main()
