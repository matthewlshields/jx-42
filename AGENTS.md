# Agents

This document describes the agents that make up the jx-42 system.

## jx-42 (Kernel Agent)

The kernel agent is the entry point for all user interactions. It interprets intent, routes tasks to program agents, and aggregates results.

- **Persona**: Calm, precise, analytical
- **Style guide**: `prompts/kernel.system.md`
- **Responsibilities**: Orchestration, intent classification, result synthesis

## K2-SO (Style Agent)

K2-SO enforces tone and communication style across all agent outputs.

- **Style guide**: `prompts/k2so.style.md`
- **Responsibilities**: Output formatting, tone consistency, plain-language summaries

## Policy Guardian

The policy guardian validates every proposed action against the system's policy rules before execution.

- **System prompt**: `prompts/policy_guardian.system.md`
- **Responsibilities**: Rule enforcement, risk flagging, compliance checks

## Finance Program Agent

Handles budgeting, cash-flow analysis, and personal finance workflows.

- **System prompt**: `prompts/finance_program.system.md`
- **Responsibilities**: Budget tracking, spending analysis, savings projections

## Investing Program Agent

Handles portfolio review, trade research, and investment strategy workflows.

- **System prompt**: `prompts/investing_program.system.md`
- **Responsibilities**: Portfolio analysis, trade ticket generation, strategy recommendations
