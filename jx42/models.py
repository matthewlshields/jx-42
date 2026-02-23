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


# ---------------------------------------------------------------------------
# Finance data models (Milestone 1)
# ---------------------------------------------------------------------------


@dataclass
class FinanceLedgerEntry:
    entry_id: str
    date: str  # YYYY-MM-DD
    amount: float  # positive = credit, negative = debit
    currency: str
    account_id: str
    merchant: str = ""
    category: str = "uncategorized"
    category_confidence: float = 0.0
    memo: str = ""
    source: str = "bank_export"  # bank_export | manual
    import_batch_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "date": self.date,
            "amount": self.amount,
            "currency": self.currency,
            "account_id": self.account_id,
            "merchant": self.merchant,
            "category": self.category,
            "category_confidence": self.category_confidence,
            "memo": self.memo,
            "source": self.source,
            "import_batch_id": self.import_batch_id,
        }


@dataclass(frozen=True)
class AnomalyAlert:
    entry_id: str
    date: str
    amount: float
    category: str
    reason: str  # spike | subscription_creep | unusual_merchant


@dataclass(frozen=True)
class RunwayEstimate:
    months: float
    monthly_burn: float
    current_balance: float
    survival_budget: float
    assumptions: str


@dataclass(frozen=True)
class DebtPayoffScenario:
    account_id: str
    balance: float
    monthly_payment: float
    months_to_payoff: float
    total_interest: float
    strategy: str  # avalanche | snowball


@dataclass(frozen=True)
class FinanceReport:
    period: str  # e.g. "2026-01" or "2026-W03"
    report_type: str  # monthly | weekly | anomaly | runway | debt_payoff
    total_income: float
    total_expenses: float
    net: float
    top_categories: List[Dict[str, Any]]
    anomalies: List[AnomalyAlert]
    runway: Optional[RunwayEstimate]
    debt_scenarios: List[DebtPayoffScenario]
    summary: str


# ---------------------------------------------------------------------------
# Investing data models (Milestone 2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StrategyRule:
    rule_id: str
    description: str
    rule_type: str  # entry | exit | position_size | kill_switch
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StrategyDefinition:
    strategy_id: str
    name: str
    version: str
    universe: List[str]
    rules: List[StrategyRule] = field(default_factory=list)
    max_position_size: float = 0.01  # fraction of portfolio
    max_open_positions: int = 3
    max_drawdown_pct: float = 0.10  # kill-switch threshold


@dataclass(frozen=True)
class MarketDataPoint:
    symbol: str
    date: str  # YYYY-MM-DD
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class TradeSignal:
    symbol: str
    date: str
    signal_type: str  # entry | exit | hold
    rule_id: str
    score: float  # 0..1
    rationale: str


@dataclass(frozen=True)
class BacktestTrade:
    symbol: str
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    qty: float
    pnl: float
    rule_id: str


@dataclass(frozen=True)
class BacktestResult:
    strategy_id: str
    start_date: str
    end_date: str
    trades: List[BacktestTrade]
    total_return: float
    max_drawdown: float
    win_rate: float
    num_trades: int
    summary: str


@dataclass
class InvestingTradeTicketDraft:
    ticket_id: str
    created_at: str
    symbol: str
    side: str  # buy | sell
    order_type: str  # market | limit | stop | stop_limit
    strategy_version: str
    status: str = "draft"
    qty: Optional[float] = None
    notional: Optional[float] = None
    entry_rule_reference: str = ""
    exit_rule_reference: str = ""
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    time_in_force: str = "day"
    risk_notes: str = ""
    sizing_rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "created_at": self.created_at,
            "symbol": self.symbol,
            "side": self.side,
            "order_type": self.order_type,
            "strategy_version": self.strategy_version,
            "status": self.status,
            "qty": self.qty,
            "notional": self.notional,
            "entry_rule_reference": self.entry_rule_reference,
            "exit_rule_reference": self.exit_rule_reference,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "time_in_force": self.time_in_force,
            "risk_notes": self.risk_notes,
            "sizing_rationale": self.sizing_rationale,
        }
