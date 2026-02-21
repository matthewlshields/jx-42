# Threat Model (Lite)

A lightweight threat model for the jx-42 system following the STRIDE framework.

## Assets

| Asset                  | Sensitivity | Notes                                      |
|------------------------|-------------|--------------------------------------------|
| User financial data    | High        | Account balances, transaction history      |
| Trade tickets          | High        | Proposed or executed trades                |
| Audit log              | High        | Tamper-evidence is critical for compliance |
| Agent system prompts   | Medium      | Leaking prompts could aid prompt injection |
| LLM API credentials    | High        | Compromise enables arbitrary LLM usage     |

## Threat Scenarios (STRIDE)

### Spoofing
- **T-01**: A malicious actor crafts input that impersonates an authorised agent.
  - *Mitigation*: Agent identity is verified via system-prompt binding; no cross-agent trust without explicit handoff.

### Tampering
- **T-02**: An attacker modifies audit log entries to cover tracks.
  - *Mitigation*: Append-only log storage; cryptographic signatures on audit events (planned M4).

### Repudiation
- **T-03**: A user denies approving an irreversible action.
  - *Mitigation*: Every human-approval gate emits a signed AuditEvent capturing user intent and timestamp.

### Information Disclosure
- **T-04**: PII leaks into audit logs or LLM context.
  - *Mitigation*: Policy P-03 mandates PII redaction before logging; automated PII scanning in CI (planned M4).

- **T-05**: System prompts are extracted via prompt-injection attacks.
  - *Mitigation*: System prompts are never echoed to users; output filtering via K2-SO style layer.

### Denial of Service
- **T-06**: Flood of requests exhausts LLM API quota.
  - *Mitigation*: Rate limiting and request queuing at the Kernel layer (planned M2).

### Elevation of Privilege
- **T-07**: A finance-scoped agent is manipulated into executing investing actions.
  - *Mitigation*: Least-privilege policy (P-05); agents only have access to their designated tool sets.

- **T-08**: Prompt injection causes the Policy Guardian to approve a vetoed action.
  - *Mitigation*: Policy Guardian operates on structured data, not free-form text; input sanitisation at ingestion.

## Residual Risks

| Risk  | Likelihood | Impact | Accepted? |
|-------|-----------|--------|-----------|
| T-05 (prompt leak)  | Low | Medium | Yes — mitigated by output filtering |
| T-06 (quota DoS)    | Medium | Low | Yes — rate limiting planned for M2 |
| T-08 (prompt inject)| Low | High | No — further hardening required in M4 |

## Next Steps

- [ ] Implement cryptographic signing for AuditEvent records (M4)
- [ ] Automated PII scanning in CI pipeline (M4)
- [ ] Red-team exercise on prompt injection vectors (M4)
- [ ] Full STRIDE review with security team before M5 release
