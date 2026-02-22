from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .models import Intent, PolicyDecisionType, RiskLevel, ToolCall


@dataclass(frozen=True)
class PolicyDecision:
    decision: PolicyDecisionType
    risk_level: RiskLevel
    rationale: str


class PolicyGuardian:
    def evaluate(self, intent: Intent, tool_call: Optional[ToolCall] = None) -> PolicyDecision:
        raise NotImplementedError


class DefaultPolicyGuardian(PolicyGuardian):
    def __init__(self) -> None:
        self._allowed_tools: set[str] = set()

    def evaluate(self, intent: Intent, tool_call: Optional[ToolCall] = None) -> PolicyDecision:
        if tool_call is not None:
            if tool_call.name not in self._allowed_tools:
                return PolicyDecision(
                    decision=PolicyDecisionType.DENY,
                    risk_level=RiskLevel.HIGH,
                    rationale="Unknown tool call denied by default.",
                )

        if intent == Intent.MONEY_MOVE:
            return PolicyDecision(
                decision=PolicyDecisionType.DENY,
                risk_level=RiskLevel.HIGH,
                rationale="Money movement is blocked in v1.",
            )
        if intent == Intent.INVESTING_TRADE_REQUEST:
            return PolicyDecision(
                decision=PolicyDecisionType.ALLOW,
                risk_level=RiskLevel.MEDIUM,
                rationale="Draft-only investing outputs are allowed.",
            )
        if intent == Intent.FINANCE_REPORT_REQUEST:
            return PolicyDecision(
                decision=PolicyDecisionType.ALLOW,
                risk_level=RiskLevel.LOW,
                rationale="Finance summaries are allowed.",
            )
        return PolicyDecision(
            decision=PolicyDecisionType.ALLOW,
            risk_level=RiskLevel.LOW,
            rationale="General requests are allowed.",
        )
