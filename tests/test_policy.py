import unittest

from jx42.models import Intent, PolicyDecisionType, ToolCall
from jx42.policy import DefaultPolicyGuardian


class TestPolicyGuardian(unittest.TestCase):
    def setUp(self) -> None:
        self.guardian = DefaultPolicyGuardian()

    def test_unknown_tool_denied(self) -> None:
        decision = self.guardian.evaluate(Intent.GENERIC_REQUEST, tool_call=ToolCall(name="unknown"))
        self.assertEqual(PolicyDecisionType.DENY, decision.decision)

    def test_money_move_denied(self) -> None:
        decision = self.guardian.evaluate(Intent.MONEY_MOVE)
        self.assertEqual(PolicyDecisionType.DENY, decision.decision)

    def test_finance_summary_allowed(self) -> None:
        decision = self.guardian.evaluate(Intent.FINANCE_REPORT_REQUEST)
        self.assertEqual(PolicyDecisionType.ALLOW, decision.decision)


if __name__ == "__main__":
    unittest.main()
