# Diagrams

## System Context Diagram (what exists and how it touches the world)

```
+------------------+        +-------------------+
|   You (Matt)     |        |  External Systems |
| voice/chat/web   |        | banks/brokerages  |
+--------+---------+        | email/calendar    |
         |                  | files/spreadsheets|
         v                  +---------+---------+
+---------------------------+                    ^
|     Interface Layer       |                    |
|  (Voice UI / Chat UI /    |                    |
|   Mobile / Web / CLI)     |                    |
+-------------+-------------+                    |
              |                                  |
              v                                  |
+---------------------------+                    |
|     JX-42 Kernel          |--------------------+
|  intent -> plan -> route  |  via Tool Connectors
+------+------+-------------+
       |      |
       |      v
       |  +------------------------+
       |  |   Policy Guardian      |
       |  | allow/deny/confirm     |
       |  +------------------------+
       |
       v
+---------------------------+
|   Programs (Agents)       |
| Finance / Investing / ... |
+------+------+-------------+
       |
       v
+---------------------------+
| Data Layer                |
| Memory Store              |
| Operational State         |
| Immutable Audit Log       |
+---------------------------+
```

## Component Diagram (inside JX-42)

```
                   +------------------------+
                   |      Interface         |
                   | (chat/voice/web/cli)  |
                   +-----------+------------+
                               |
                               v
+------------------------------------------------------------------+
|                           JX-42 Kernel                            |
|------------------------------------------------------------------|
|  Intent Router | Planner | Tool Selector | Response Composer       |
|------------------------------------------------------------------|
|                 calls -> Policy Guardian (required)               |
+----------------------+-------------------------------+------------+
                       |                               |
                       v                               v
              +------------------+            +----------------------+
              | Memory Librarian |            |   Programs (Agents)  |
              | retrieve/store   |            | Finance / Investing  |
              +------------------+            +----------------------+
                       |                               |
                       v                               v
              +------------------+            +----------------------+
              |   Data Layer     |            |   Tool Connectors    |
              | memory/state/log |            | email/bank/broker/...|
              +------------------+            +----------------------+
```

## Data Flow Diagram (Finance + Investing)

```
          (Exports/APIs)
 Banks/Cards/Payroll -----> [Ingest] -----> [Normalize] -----> [Ledger]
                                     |                |
                                     v                v
                                 [Categorize]     [Reconcile]
                                     |                |
                                     v                v
                                  [KPIs] -------> [Reports]
                                     |
                                     v
                                 [Plans/Drafts]
                                     |
                                     v
                              Policy Guardian Gate
                                     |
                          +----------+----------+
                          |                     |
                          v                     v
                    Draft-only outputs      Confirmed actions
                   (budgets, payoff,       (future: execute)
                    trade tickets)
```

## Sequence Diagram: “Hey Jax, can I retire at 62?”

```
You -> Interface: Ask question
Interface -> Kernel: request + context
Kernel -> Memory: retrieve finance profile + goals
Kernel -> Finance Program: compute cashflow, runway, projections
Finance Program -> Data Layer: read ledger + balances
Finance Program -> Kernel: projections + assumptions + report
Kernel -> Policy Guardian: check if any tool calls / risky actions
Policy Guardian -> Kernel: allow (read-only)
Kernel -> Interface: K-2SO response + report + next actions
Kernel -> Audit Log: record decision trail
```

## Sequence Diagram: “Hey Jax, place this trade” (future, guarded)

```
You -> Interface: request trade
Interface -> Kernel
Kernel -> Investing Program: generate trade ticket + sizing
Investing Program -> Kernel: draft ticket + rationale
Kernel -> Policy Guardian: risk check (size, account, new instrument)
Policy Guardian -> Kernel: requires confirm + second confirm if above threshold
Kernel -> Interface: show draft + ask confirm
You -> Interface: confirm
Kernel -> Tool Connector: place order (only after confirm)
Tool Connector -> Kernel: execution result
Kernel -> Audit Log: record tool call + outcome
Kernel -> Interface: confirmation + monitoring plan
```