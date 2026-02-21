# Decision Log

This log records significant architectural and design decisions made during the development of jx-42.

---

## ADR-001: Agent-per-Program Pattern

**Date**: 2026-02-21
**Status**: Accepted

### Context
We need to handle both personal finance and investing workflows without creating a monolithic agent that is difficult to test and maintain.

### Decision
Separate program agents (Finance, Investing) are orchestrated by the Kernel agent. Each program agent has its own system prompt and data schema.

### Consequences
- **Positive**: Clear separation of concerns; each agent can be updated independently.
- **Negative**: Orchestration overhead; the Kernel must correctly route all intents.

---

## ADR-002: Policy Guardian as a Veto Layer

**Date**: 2026-02-21
**Status**: Accepted

### Context
Regulatory and risk requirements demand that no irreversible action is taken without compliance validation.

### Decision
All proposed actions are passed through the `policy_guardian` agent before execution. The guardian has unconditional veto power.

### Consequences
- **Positive**: Single enforcement point for all policies; easy to audit.
- **Negative**: Adds latency to every action; policy rules must be kept up to date.

---

## ADR-003: JSON Schema for Data Contracts

**Date**: 2026-02-21
**Status**: Accepted

### Context
Agents exchange structured data. We need a language-agnostic way to define and validate these contracts.

### Decision
JSON Schema (Draft-07) is used for all data contracts (`schemas/` directory).

### Consequences
- **Positive**: Widely supported; validators available in all major languages.
- **Negative**: JSON Schema can be verbose for complex nested types.

---

## ADR-004: Append-Only Audit Log

**Date**: 2026-02-21
**Status**: Accepted

### Context
Compliance requirements demand a tamper-evident record of all agent actions.

### Decision
The audit logger writes append-only `AuditEvent` records. No audit record may be modified or deleted except by an authorised retention-expiry process.

### Consequences
- **Positive**: Immutability gives strong guarantees for compliance and forensics.
- **Negative**: Storage grows over time; retention policies must be enforced.
