from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PolicyDecisionType(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    CONFIRM_REQUIRED = "confirm_required"


class Intent(str, Enum):
    FINANCE_REPORT_REQUEST = "finance_report_request"
    INVESTING_TRADE_REQUEST = "investing_trade_request"
    MONEY_MOVE = "money_move"
    GENERIC_REQUEST = "generic_request"


@dataclass(frozen=True)
class UserRequest:
    text: str
    user_id: Optional[str] = None


@dataclass(frozen=True)
class KernelResponse:
    correlation_id: str
    response_text: str
    audit_event_ids: List[str]


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Plan:
    intent: Intent
    plan_summary: str
    tool_calls: List[ToolCall] = field(default_factory=list)


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    timestamp: str
    correlation_id: str
    component: str
    action_type: str
    risk_level: RiskLevel
    inputs_summary: str
    outputs_summary: str
    policy_decision: PolicyDecisionType
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "component": self.component,
            "action_type": self.action_type,
            "risk_level": self.risk_level.value,
            "inputs_summary": self.inputs_summary,
            "outputs_summary": self.outputs_summary,
            "policy_decision": self.policy_decision.value,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class MemoryItem:
    item_id: str
    timestamp: str
    item_type: str
    content: str
    provenance: str


class IdGenerator:
    def __init__(self, rng: Optional[random.Random] = None) -> None:
        self._rng = rng

    def new_uuid(self) -> str:
        if self._rng is None:
            return str(uuid.uuid4())
        value = self._rng.getrandbits(128)
        return str(uuid.UUID(int=value))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
