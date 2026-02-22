# JX-42 Data Model (v1)

## 1 AuditEvent (append-only)
Fields:
- event_id (uuid)
- timestamp (iso8601)
- correlation_id (uuid) - ties multiple events to a single request
- component (kernel|policy|memory|finance|investing|connector)
- action_type (plan_created|tool_call|policy_decision|report_generated|draft_created|error)
- risk_level (low|medium|high)
- inputs_summary (redacted)
- outputs_summary (redacted)
- policy_decision (allow|deny|confirm_required)
- rationale (short)

## 2 Finance Ledger Entry
Fields:
- entry_id (uuid)
- date
- amount
- currency
- account_id
- merchant/payee
- category (normalized)
- category_confidence (0..1)
- memo
- source (bank_export|manual)
- import_batch_id

## 3 Investing Trade Ticket (draft)
Fields:
- ticket_id (uuid)
- created_at
- symbol
- side (buy|sell)
- order_type (market|limit|stop|stop_limit)
- qty / notional
- entry_rule_reference
- exit_rule_reference
- stop_loss (optional)
- take_profit (optional)
- time_in_force
- risk_notes
- sizing_rationale
- strategy_version
- status (draft|approved|placed|canceled)  # placed not used in v1