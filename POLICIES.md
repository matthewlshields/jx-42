# Policies

This document defines the operational policies governing all jx-42 agents.

## P-01: Human-in-the-Loop for Irreversible Actions

Any action that is irreversible (e.g., submitting a trade, transferring funds) **must** receive explicit human confirmation before execution.

## P-02: Audit All Agent Actions

Every agent action, decision, and tool call must emit a structured `AuditEvent` conforming to `schemas/audit_event.schema.json`.

## P-03: No PII in Logs

Agent logs and audit events must not contain personally identifiable information (PII). Redact or tokenize sensitive fields before logging.

## P-04: Policy Guardian Veto

The `policy_guardian` agent has unconditional veto power over any proposed action. A vetoed action must be logged and surfaced to the user with a plain-language explanation.

## P-05: Least Privilege

Agents must only request the minimum data and tool permissions required to complete their assigned task.

## P-06: Transparency

Agents must be able to explain their reasoning in plain language upon request.

## P-07: Data Retention

Conversation and audit data is retained for 90 days unless a shorter period is required by applicable law or user request.
