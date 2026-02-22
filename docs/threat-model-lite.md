# Threat Model Lite (v1)

## Assets
- Financial data (transactions, balances)
- Strategy definitions and trade drafts
- Audit log (integrity-critical)
- Credentials/tokens (future)

## Primary Risks
- Unauthorized actions (money movement)
- Data exfiltration via prompts/logs
- Hallucinated outputs causing bad decisions
- Connector compromise

## Mitigations
- Policy Guardian gating for all external calls
- Draft-only for finance/investing execution
- Append-only audit log with correlation IDs
- Redaction of secrets in inputs_summary/outputs_summary