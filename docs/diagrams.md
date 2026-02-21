# Diagrams

## System Context Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                          jx-42 System                            │
│                                                                  │
│  ┌────────────┐    ┌───────────────────┐    ┌────────────────┐  │
│  │  Kernel    │───▶│  Program Agents   │───▶│Policy Guardian │  │
│  │  (jx-42)  │    │  Finance/Investing │    │                │  │
│  └────────────┘    └───────────────────┘    └───────┬────────┘  │
│         ▲                                           │            │
│         │                                           ▼            │
│  ┌──────┴───────┐                         ┌─────────────────┐   │
│  │  User Input  │                         │  Audit Logger   │   │
│  └──────────────┘                         └─────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

## Agent Interaction Sequence

```
User ──▶ Kernel ──▶ Intent Classifier
                         │
               ┌─────────┴──────────┐
               ▼                    ▼
         Finance Agent       Investing Agent
               │                    │
               └─────────┬──────────┘
                         ▼
                  Policy Guardian
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
           Approved              Vetoed
              │                     │
              ▼                     ▼
         K2-SO Format         Notify User
              │
              ▼
           User ◀──── Response
```

## Schema Relationship Diagram

```
AuditEvent
  └── payload → FinanceLedger | InvestingTradeTicket | (other)

FinanceLedger
  └── account_id (opaque reference to external account)

InvestingTradeTicket
  └── symbol (references external market data)
```
