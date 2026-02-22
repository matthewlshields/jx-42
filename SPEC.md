# JX-42 System Specification (Tool/Model Agnostic)

## 1. Goals
- Provide a personal assistant that can plan and execute tasks safely.
- Prioritize finance + investing capabilities after the foundational core.
- Ensure auditability, reproducibility, and controlled permissions.

## 2. Non-Goals (v1)
- Autonomous financial execution (no trades/transfers/autopay changes).
- Unbounded “agent swarm” behavior.
- Hidden actions without explicit user visibility.

## 3. High-Level Architecture
Layers:
1) Interface Layer: chat/voice/web/mobile/CLI
2) Brain Layer: Kernel (orchestrator)
3) Programs Layer: specialist Agents
4) Tools Layer: connectors to external systems
5) Data Layer: Memory Store, Operational State, Immutable Audit Log

## 4. Core Components
### 4.1 Kernel (Orchestrator)
Responsibilities:
- Interpret user request → create goal + plan
- Retrieve context via Memory Librarian
- Route plan steps to Programs/Tools
- Enforce policy gate before any action
- Compose responses (planner voice → K-2SO delivery voice)
- Emit audit events for all decisions and actions

Hard rules:
- Must call Policy Guardian before any tool/action (including reads from external systems)
- Must produce audit event IDs in responses (for traceability)
- Must separate planning content from persona styling

### 4.2 Policy Guardian
Responsibilities:
- Evaluate proposed plan steps + tool calls
- Enforce permissions tiers and confirmation requirements
- Block unknown tools/connectors by default
- Maintain “blast radius” controls for sensitive domains (finance/investing)

### 4.3 Memory Librarian
Responsibilities:
- Store/retrieve:
  - user preferences, goals, risk limits
  - SOPs (how Jax should behave)
  - financial assumptions (income, fixed bills, thresholds)
  - investing strategy definitions and constraints
- Provide retrieval bundles with provenance (source pointers to notes/audit entries)

## 5. Programs (Agents)
Tier 0:
- Kernel, Policy Guardian, Memory Librarian

Tier 1:
- Finance Program
- Investing Program

## 6. Finance Program (v1)
Inputs:
- CSV exports (banks/cards/payroll)
- Manual entries (income, recurring bills, adjustments)

Outputs:
- Cashflow summary (monthly + weekly deltas)
- Debt snapshot + payoff scenarios (draft plans)
- Runway estimate + survival budget draft
- Anomaly report (spend spikes, fees, subscriptions)
- Action list ranked by impact

Constraints:
- Draft-only. No account changes or payments without explicit approvals and future connector implementation.

## 7. Investing Program (v1)
Inputs:
- Market data feed (single source initially)
- Strategy definition (rules-based)
- Portfolio snapshot (positions + cash)
- Risk settings (max position size, max drawdown, cooldown rules)

Outputs:
- Watchlist scored by strategy signals
- Backtest report (simple, transparent)
- Trade candidates with entry/exit/sizing/rationale
- Draft trade tickets (never placed in v1)

Constraints:
- Draft-only. Paper trading recommended before any live execution capability is enabled.

## 8. Observability & Audit
All components emit AuditEvents (see DATA_MODEL.md).
Minimum fields:
- timestamp, component, action_type, inputs_summary, outputs_summary, risk_level, policy_decision, correlation_id

## 9. Personas
- Planner Voice: precise, clinical, safety-first
- K-2SO Voice: blunt/sarcastic presentation-only layer applied after planning