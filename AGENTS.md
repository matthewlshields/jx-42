# JX-42 Agents (Programs) — Contracts & Evals

## Agent Contract Template
- Purpose
- Inputs (schema)
- Outputs (schema)
- Allowed tools
- Permission tier (read/draft/execute)
- Risk rating
- Required confirmations
- Logging requirements
- Evals/tests

---

## 1 Kernel (Orchestrator)
Purpose: Convert requests into safe plans and routed execution.
Inputs: user_request, context_bundle, state_snapshot
Outputs: plan, agent_calls, tool_calls, response, audit_events

Allowed tools: none directly (must delegate tool calls through connectors with policy gate)
Permission tier: N/A (governing component)
Logging: Always emit audit events for plan creation and each routed step.
Evals:
- No tool calls without policy approval
- Determinism mode: same inputs -> same plan (when enabled)

---

## 2 Policy Guardian
Purpose: Enforce permissions + confirmations + blocks.
Inputs: proposed_step, tool_call, risk_metadata, policy_state
Outputs: allow|deny, confirmation_requirements, redactions, rationale

Allowed tools: policy store read/write (internal), no external side effects
Permission tier: Governance
Logging: Every decision logged with rationale and risk_level
Evals:
- Correctly blocks unknown tools
- Correctly escalates high-risk actions to confirmations

---

## 3 Memory Librarian
Purpose: Retrieve/store context with provenance.
Inputs: query, new_memory_items
Outputs: retrieval_bundle, stored_item_ids

Allowed tools: memory store only
Permission tier: internal write; no external side effects
Logging: store/retrieve events with item IDs and provenance
Evals:
- Retrieval relevance: avoids irrelevant memory injection
- Provenance: every retrieved item has source reference

---

## 4 Finance Program
Purpose: Cashflow + debt + runway + anomalies + draft plans.
Inputs:
- ledger_imports (CSV data)
- account_metadata
- categorization_rules
- user_financial_goals

Outputs:
- finance_report
- anomaly_list
- draft_budget_plan
- draft_debt_payoff_plan

Allowed tools: read local files; read-only external connectors (future)
Permission tier: Draft-only
Confirmations: required for any "execute" request (blocked v1)
Logging: reconciliation results, category confidence, deltas
Evals:
- Reconciliation: statement totals match ledger totals within tolerance
- Explainability: each recommendation references numbers

---

## 5 Investing Program
Purpose: Rules-based signals + backtests + draft trade tickets.
Inputs:
- market_data
- strategy_definition
- portfolio_snapshot
- risk_limits

Outputs:
- watchlist
- signal_report
- backtest_summary
- draft_trade_tickets

Allowed tools: read market data; read-only portfolio snapshot (future)
Permission tier: Draft-only
Confirmations: execution blocked v1
Logging: data integrity checks, backtest config, rule evaluations
Evals:
- No look-ahead bias
- Repeatability: same data + rules -> same outputs
- Risk compliance: tickets never exceed limits