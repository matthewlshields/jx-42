# Milestones

## M0 — Foundation (Current)

- [x] Repository structure created
- [x] Core documentation: SPEC, AGENTS, POLICIES, DATA_MODEL, ARCHITECTURE
- [x] JSON schemas for AuditEvent, FinanceLedger, InvestingTradeTicket
- [x] System prompts for all agents
- [x] Example inputs and strategy documents

## M1 — Kernel Prototype

- [ ] Implement jx-42 kernel agent with intent classification
- [ ] Integrate policy_guardian veto loop
- [ ] Emit AuditEvent records for every agent action
- [ ] Basic CLI runner for local testing

## M2 — Finance Program

- [ ] Budget ingestion from CSV/JSON ledger
- [ ] Spending analysis and categorisation
- [ ] Monthly savings projection output
- [ ] Unit tests with `finance_sample_inputs.md` data

## M3 — Investing Program

- [ ] Portfolio summary from trade ticket history
- [ ] Trade proposal workflow with human-approval gate
- [ ] Strategy recommendation narrative generation
- [ ] Integration tests with `investing_strategy_example.md`

## M4 — Hardening & Observability

- [ ] Full policy compliance audit
- [ ] PII redaction validation
- [ ] Structured logging with AuditEvent schema
- [ ] Threat model review (see `docs/threat-model-lite.md`)

## M5 — Release Candidate

- [ ] End-to-end integration tests
- [ ] Documentation review and finalisation
- [ ] Security sign-off
- [ ] Version tag `v1.0.0`
