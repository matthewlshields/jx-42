# JX-42 Milestones (Build Order)

## Milestone 0 — Kernel Skeleton (Tier 0)
Deliver:
- Request -> Plan -> Route loop
- Policy Guardian gate enforced
- Memory store stub + retrieval bundle
- Audit log events for each step

Accept:
- No tool calls without policy approval
- Responses include correlation_id + audit_event_id
- Determinism mode option for planning

## Milestone 1 — Finance v1 (Tier 1)
Deliver:
- CSV import pipeline
- Normalization + categorization (simple rules first)
- Reconciliation checks
- Weekly delta report + monthly close
- Runway + survival budget draft
- Draft debt payoff scenarios

Accept:
- Ledger totals reconcile with statement totals within tolerance
- Every recommendation cites numeric basis
- Anomaly detection flags spikes/subscription creep

## Milestone 2 — Investing v1 (Tier 1)
Deliver:
- Strategy definition format (rules-based)
- Market data ingestion (single source)
- Data integrity checks
- Backtest v1 (simple, transparent)
- Watchlist + signals
- Draft trade tickets

Accept:
- No look-ahead bias
- Repeatable outputs (same inputs => same outputs)
- Tickets respect risk limits

## Milestone 3 — UX + Safety Upgrades
Deliver:
- Confirmation flows (single/double confirm)
- Paper trading mode
- Kill-switch + cooldown rules
- Better dashboards + exportable reports