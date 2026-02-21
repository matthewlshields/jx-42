# Data Model

This document describes the core data entities used by jx-42.

## AuditEvent

Represents a single recorded action or decision by an agent. Schema: `schemas/audit_event.schema.json`.

| Field        | Type     | Description                                      |
|--------------|----------|--------------------------------------------------|
| event_id     | string   | UUID v4 identifier for the event                 |
| timestamp    | string   | ISO 8601 datetime of the event                   |
| agent        | string   | Name of the agent that produced the event        |
| action       | string   | Short action identifier (e.g., `trade.propose`)  |
| status       | string   | `success`, `failure`, `vetoed`, or `pending`     |
| payload      | object   | Action-specific data (schema varies by action)   |
| policy_flags | string[] | List of policy IDs checked during this event     |

## FinanceLedger

Represents a financial account ledger entry. Schema: `schemas/finance_ledger.schema.json`.

| Field          | Type   | Description                              |
|----------------|--------|------------------------------------------|
| entry_id       | string | UUID v4 identifier                       |
| account_id     | string | Opaque account reference                 |
| date           | string | ISO 8601 date of the transaction         |
| description    | string | Human-readable description               |
| amount         | number | Transaction amount (negative = debit)    |
| currency       | string | ISO 4217 currency code (e.g., `USD`)     |
| category       | string | Spending/income category                 |
| running_balance| number | Account balance after this entry         |

## InvestingTradeTicket

Represents a proposed or executed trade. Schema: `schemas/investing_trade_ticket.schema.json`.

| Field        | Type   | Description                                    |
|--------------|--------|------------------------------------------------|
| ticket_id    | string | UUID v4 identifier                             |
| symbol       | string | Ticker symbol (e.g., `AAPL`)                   |
| asset_class  | string | `equity`, `etf`, `bond`, `crypto`, `other`     |
| action       | string | `buy` or `sell`                                |
| quantity     | number | Number of shares or units                      |
| limit_price  | number | Optional limit price; null for market orders   |
| currency     | string | ISO 4217 currency code                         |
| rationale    | string | Agent-generated plain-language rationale       |
| status       | string | `proposed`, `approved`, `rejected`, `executed` |
| created_at   | string | ISO 8601 datetime                              |
