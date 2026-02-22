import unittest
from unittest.mock import patch

from jx42.audit import InMemoryAuditLog
from jx42.kernel import DefaultKernel, KernelConfig
from jx42.memory import InMemoryMemoryLibrarian
from jx42.models import Intent, Plan, ToolCall, UserRequest
from jx42.policy import DefaultPolicyGuardian


class TestKernel(unittest.TestCase):
    def setUp(self) -> None:
        self.guardian = DefaultPolicyGuardian()
        self.librarian = InMemoryMemoryLibrarian()
        self.audit = InMemoryAuditLog()

    def test_handle_request_plan_created(self) -> None:
        kernel = DefaultKernel(
            policy_guardian=self.guardian,
            memory_librarian=self.librarian,
            audit_log=self.audit,
        )
        request = UserRequest(text="Hey Jax, summarize my finances")
        response = kernel.handle_request(request)
        self.assertIsNotNone(response.correlation_id)
        self.assertEqual(3, len(response.audit_event_ids))
        events = self.audit.list_events(correlation_id=response.correlation_id)
        self.assertEqual(3, len(events))
        self.assertEqual("plan_created", events[0].action_type)
        self.assertEqual("policy_decision", events[1].action_type)
        self.assertEqual("response_generated", events[2].action_type)

    def test_money_move_denied(self) -> None:
        kernel = DefaultKernel(
            policy_guardian=self.guardian,
            memory_librarian=self.librarian,
            audit_log=self.audit,
        )
        request = UserRequest(text="Hey Jax, move $500 to savings")
        response = kernel.handle_request(request)
        self.assertIn("blocked", response.response_text.lower())

    def test_determinism(self) -> None:
        kernel1 = DefaultKernel(
            policy_guardian=self.guardian,
            memory_librarian=self.librarian,
            audit_log=InMemoryAuditLog(),
            config=KernelConfig(determinism_seed=42),
            time_provider=lambda: "2026-01-01T00:00:00+00:00",
        )
        kernel2 = DefaultKernel(
            policy_guardian=self.guardian,
            memory_librarian=self.librarian,
            audit_log=InMemoryAuditLog(),
            config=KernelConfig(determinism_seed=42),
            time_provider=lambda: "2026-01-01T00:00:00+00:00",
        )
        request = UserRequest(text="test")
        response1 = kernel1.handle_request(request)
        response2 = kernel2.handle_request(request)
        self.assertEqual(response1.correlation_id, response2.correlation_id)

    def test_tool_call_gated_by_policy(self) -> None:
        """Verify that tool calls are gated by Policy Guardian."""
        kernel = DefaultKernel(
            policy_guardian=self.guardian,
            memory_librarian=self.librarian,
            audit_log=self.audit,
        )
        # Patch _plan_request to return a plan with an unknown tool call
        with patch.object(kernel, "_plan_request") as mock_plan:
            mock_plan.return_value = Plan(
                intent=Intent.GENERIC_REQUEST,
                plan_summary="Test plan with unknown tool",
                tool_calls=[ToolCall(name="unknown_tool", args={})],
            )
            request = UserRequest(text="test with unknown tool")
            response = kernel.handle_request(request)
            # Unknown tools should be denied by policy
            self.assertIn("blocked", response.response_text.lower())
            # Verify policy decision event was created
            events = self.audit.list_events(correlation_id=response.correlation_id)
            policy_events = [e for e in events if e.component == "policy"]
            self.assertGreater(len(policy_events), 0)
            self.assertEqual("deny", policy_events[0].policy_decision.value)


if __name__ == "__main__":
    unittest.main()
