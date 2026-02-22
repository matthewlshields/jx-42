from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, List, Optional

from .audit import AuditLog
from .memory import MemoryLibrarian
from .models import (
    AuditEvent,
    IdGenerator,
    Intent,
    KernelResponse,
    Plan,
    PolicyDecisionType,
    RiskLevel,
    UserRequest,
    utc_now_iso,
)
from .policy import PolicyDecision, PolicyGuardian


@dataclass(frozen=True)
class KernelConfig:
    determinism_seed: Optional[int] = None
    persona: str = "k2so"


class Kernel:
    def handle_request(self, request: UserRequest) -> KernelResponse:
        raise NotImplementedError


class DefaultKernel(Kernel):
    def __init__(
        self,
        policy_guardian: PolicyGuardian,
        memory_librarian: MemoryLibrarian,
        audit_log: AuditLog,
        config: Optional[KernelConfig] = None,
        time_provider: Optional[Callable[[], str]] = None,
    ) -> None:
        self._policy = policy_guardian
        self._memory = memory_librarian
        self._audit = audit_log
        self._config = config or KernelConfig()
        self._rng = random.Random(self._config.determinism_seed)
        self._id_generator = IdGenerator(self._rng if self._config.determinism_seed is not None else None)
        self._time_provider = time_provider or utc_now_iso

    def handle_request(self, request: UserRequest) -> KernelResponse:
        correlation_id = self._id_generator.new_uuid()
        context_items = self._memory.retrieve(query=request.text, limit=3)
        plan = self._plan_request(request, context_items)

        plan_event = self._emit_event(
            correlation_id=correlation_id,
            component="kernel",
            action_type="plan_created",
            risk_level=RiskLevel.LOW,
            inputs_summary=request.text,
            outputs_summary=plan.plan_summary,
            policy_decision=PolicyDecisionType.ALLOW,
            rationale="Plan created.",
        )

        for tool_call in plan.tool_calls:
            _ = self._policy.evaluate(plan.intent, tool_call=tool_call)

        decision = self._policy.evaluate(plan.intent, tool_call=None)

        policy_event = self._emit_event(
            correlation_id=correlation_id,
            component="policy",
            action_type="policy_decision",
            risk_level=decision.risk_level,
            inputs_summary=plan.plan_summary,
            outputs_summary=decision.decision.value,
            policy_decision=decision.decision,
            rationale=decision.rationale,
        )

        response_text = self._build_response(plan, decision)
        response_text = self._apply_persona(response_text)

        response_event = self._emit_event(
            correlation_id=correlation_id,
            component="kernel",
            action_type="response_generated",
            risk_level=decision.risk_level,
            inputs_summary=plan.plan_summary,
            outputs_summary=response_text,
            policy_decision=decision.decision,
            rationale="Response generated.",
        )

        audit_ids = [plan_event, policy_event, response_event]
        return KernelResponse(
            correlation_id=correlation_id,
            response_text=response_text,
            audit_event_ids=audit_ids,
        )

    def _plan_request(self, request: UserRequest, context_items: List[object]) -> Plan:
        text = request.text.lower()
        if "move" in text and ("$" in text or "transfer" in text or "savings" in text):
            intent = Intent.MONEY_MOVE
            plan_summary = "Plan: money_move (blocked in v1)."
        elif "summarize" in text and "finance" in text:
            intent = Intent.FINANCE_REPORT_REQUEST
            plan_summary = "Plan: finance_report_request (draft-only)."
        elif "trade" in text or "buy" in text or "sell" in text:
            intent = Intent.INVESTING_TRADE_REQUEST
            plan_summary = "Plan: investing_trade_request (draft-only)."
        else:
            intent = Intent.GENERIC_REQUEST
            plan_summary = "Plan: generic_request."

        _ = context_items
        return Plan(intent=intent, plan_summary=plan_summary, tool_calls=[])

    def _build_response(self, plan: Plan, decision: PolicyDecision) -> str:
        if decision.decision == PolicyDecisionType.DENY:
            return (
                "Request blocked by policy. "
                "I can draft a safe plan instead if you want."
            )
        if plan.intent == Intent.FINANCE_REPORT_REQUEST:
            return "Draft finance summary stub. Provide data to continue."
        if plan.intent == Intent.INVESTING_TRADE_REQUEST:
            return "Draft investing note stub. Provide strategy and risk limits to continue."
        if plan.intent == Intent.MONEY_MOVE:
            return "Money movement is blocked in v1."
        return "Request received. Draft response stub."

    def _apply_persona(self, text: str) -> str:
        if self._config.persona == "k2so":
            return text
        return text

    def _emit_event(
        self,
        correlation_id: str,
        component: str,
        action_type: str,
        risk_level: RiskLevel,
        inputs_summary: str,
        outputs_summary: str,
        policy_decision: PolicyDecisionType,
        rationale: str,
    ) -> str:
        event = AuditEvent(
            event_id=self._id_generator.new_uuid(),
            timestamp=self._time_provider(),
            correlation_id=correlation_id,
            component=component,
            action_type=action_type,
            risk_level=risk_level,
            inputs_summary=inputs_summary,
            outputs_summary=outputs_summary,
            policy_decision=policy_decision,
            rationale=rationale,
        )
        return self._audit.append(event)
