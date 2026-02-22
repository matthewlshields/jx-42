# JX-42 (Jax) — Personal Assistant Kernel + Finance/Investing Programs

JX-42 is a personal assistant system built around a safe-by-default orchestrator ("Kernel") and modular specialist programs ("Agents") with strict policy gating and audit logging.

## Priorities
Tier 0 (Foundation): Kernel, Policy Guardian, Memory Librarian  
Tier 1 (Highest): Finance Program, Investing Program  
Tier 2: Email/Calendar/Tasks later

## Non-negotiables
- No external tool/action without Policy Guardian approval
- Money moves are draft-only by default (no trading/transfers in v1)
- Every plan/tool call produces an audit event
- JX-42 voice is presentation-only (planner remains clinical)

## Quick Start (planning)
1) Read: SPEC.md, POLICIES.md
2) Implement in milestones order: MILESTONES.md
3) Keep contracts stable: DATA_MODEL.md + /schemas

## Installation & Usage

Install in development mode:
```bash
pip install -e .
```

Run a request:
```bash
jx-42 run "Hey Jax, summarize my finances"
```

Run with deterministic seed:
```bash
jx-42 run "Hey Jax, summarize my finances" --seed 42
```

## Testing

Run all tests:
```bash
python -m unittest discover -s tests -p 'test_*.py'
```

Run specific test module:
```bash
python -m unittest tests.test_kernel
```

## Glossary
- Kernel: orchestrator that routes work
- Program/Agent: specialist module with strict scope/permissions
- Tool Connector: integration to external systems (bank, broker, email, etc.)
- Audit Log: immutable record of decisions/actions