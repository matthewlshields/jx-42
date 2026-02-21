# Architecture

## High-Level Overview

```
User
 │
 ▼
┌─────────────────────────────────┐
│          jx-42 Kernel           │  ← orchestrator / intent router
└────────┬───────────┬────────────┘
         │           │
         ▼           ▼
┌──────────────┐  ┌──────────────────┐
│ Finance      │  │ Investing        │
│ Program      │  │ Program          │
│ Agent        │  │ Agent            │
└──────┬───────┘  └───────┬──────────┘
       │                  │
       └──────┬───────────┘
              ▼
     ┌─────────────────┐
     │ Policy Guardian │  ← veto / compliance layer
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │  Audit Logger   │  ← emits AuditEvent records
     └─────────────────┘
```

## Component Descriptions

### jx-42 Kernel
- Receives raw user input
- Classifies intent and selects the appropriate program agent
- Aggregates sub-agent responses and formats final output via K2-SO style rules

### Finance Program Agent
- Operates on `FinanceLedger` data
- Produces budget summaries, spending breakdowns, and savings projections

### Investing Program Agent
- Operates on `InvestingTradeTicket` data
- Produces portfolio snapshots and trade proposals

### Policy Guardian
- Sits between any proposed action and its execution
- Validates against all `POLICIES.md` rules
- Emits a `vetoed` AuditEvent and surfaces a plain-language explanation on rejection

### Audit Logger
- Receives AuditEvent objects from all agents
- Persists to the configured backend (file, database, or event stream)

### K2-SO Style Layer
- Post-processes all user-facing text
- Ensures consistent tone and plain-language accessibility

## Data Flow

1. User sends a message to the Kernel.
2. Kernel classifies intent → routes to Finance or Investing Program Agent.
3. Program Agent formulates a proposed action.
4. Policy Guardian evaluates the proposed action.
   - **Approved**: action proceeds; AuditEvent `status: success` emitted.
   - **Vetoed**: action blocked; AuditEvent `status: vetoed` emitted; user notified.
5. Approved output is formatted by K2-SO and returned to the user.

## Technology Choices

| Concern              | Choice                        | Rationale                              |
|----------------------|-------------------------------|----------------------------------------|
| Agent runtime        | TBD (LLM provider agnostic)   | Avoid lock-in; swap via config         |
| Schema validation    | JSON Schema (Draft-07)        | Widely supported, language-agnostic    |
| Audit persistence    | Append-only log / event store | Immutability guarantees for compliance |
| Configuration        | Environment variables + YAML  | 12-factor compliant                    |
