# jx-42 Specification

## Overview

jx-42 is an agentic AI system designed to assist with financial planning, investing, and audit operations. This document provides the technical specification for the system.

## Goals

- Provide a kernel agent (`jx-42`) that orchestrates finance and investing sub-agents
- Enforce policy guardrails via a dedicated `policy_guardian` agent
- Maintain a complete audit trail of all agent actions and decisions
- Support extensible program modules for finance and investing workflows

## Non-Goals

- Direct execution of trades or financial transactions without human approval
- Storage of personally identifiable information (PII) beyond what is strictly necessary

## System Boundaries

- **Input**: User instructions, market data feeds, financial account data
- **Output**: Recommendations, reports, structured audit events
- **External Dependencies**: LLM provider APIs, brokerage data connectors (read-only)

## Versioning

This spec follows [Semantic Versioning](https://semver.org/). Current version: `0.1.0`.
