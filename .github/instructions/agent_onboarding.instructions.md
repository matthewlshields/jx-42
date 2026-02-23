---
applyTo: "**"
description: Coding Agent Onboarding — Always Read System Index First
trigger: session_start
---

# Coding Agent Onboarding — Always Start with system_index.yaml

## Mandatory First Step for Every Session

**Before making any code changes, reading files, or proposing architecture changes:**

1. **Read `system_index.yaml`** — This is the machine-readable blueprint of the entire system.
   - It contains all module responsibilities, data models, constraints, and hard rules
   - It maps data flow, security models, and integration points
   - It lists schemas, entry points, and dependencies
   - **Do not reverse-engineer the codebase** — use this map instead

2. **Understand the hierarchy:**
   - Tier 0: Foundation (Kernel, Policy, Memory) — must be stable
   - Tier 1: Programs (Finance, Investing) — draft-only outputs (v1)
   - Tier 2: Future capabilities (Email, Calendar, Tasks)

3. **Know the hard constraints:**
   - No external action without Policy Guardian approval
   - Money moves are always draft-only (v1)
   - Every plan/tool call produces audit events
   - All changes must preserve contract stability (DATA_MODEL.md, /schemas)

## Workflow for Code Changes

1. Read `system_index.yaml` → understand the target module's responsibility
2. Reference `DATA_MODEL.md` → check data structures and contracts
3. Read relevant schema files in `/schemas` → validate input/output formats
4. Check `AGENTS.md` → understand permissions and evals for the module
5. Check `POLICIES.md` → understand policy gating and confirmations
6. Make focused, contract-respecting changes
7. Run `uv run pytest -v` → verify no regressions
8. Run security scan before submitting

## Key Files & Their Purpose

| File | Purpose | When to Read |
|------|---------|--------------|
| `system_index.yaml` | Machine-readable architecture map | ALWAYS — first thing |
| `AGENTS.md` | Agent contracts, permissions, evals | Understanding responsibility boundaries |
| `POLICIES.md` | Policy gating rules, confirmations | Implementing policy checks |
| `DATA_MODEL.md` | Data structures and contracts | Validating inputs/outputs |
| `SPEC.md` | System specification and non-goals | Understanding design intent |
| `schemas/*.json` | Schema validation references | Implementing data validation |
| `MILESTONES.md` | Implementation priorities | Planning work sequence |

## Don't Reverse-Engineer — Use the Map

**Bad:** "Let me read kernel.py to understand the system"
**Good:** "Let me check system_index.yaml for the Kernel module's responsibility, entry points, and hard rules"

**Bad:** "I'll search the codebase for all API entry points"
**Good:** "I'll check system_index.yaml.entrypoints for CLI and script entry points"

**Bad:** "I need to understand the data flow"
**Good:** "I'll check system_index.yaml.data_model for the complete schema map"

## Adding New Capabilities

When proposing or implementing new features:

1. **Update `system_index.yaml` first** — add to appropriate tier or module
2. **Update `AGENTS.md`** — add contract if it's a new program
3. **Update `DATA_MODEL.md`** — add data structures if needed
4. **Create schemas** in `/schemas` if introducing new data types
5. **Update README.md** if it affects user-facing behavior
6. **Document in MILESTONES.md** if it's a new milestone

**Never commit code without updating system_index.yaml when architecture changes.**

## Security Scanning

Before proposing changes:
```bash
uv run pytest -v           # Run all tests
```

If generating new code:
```bash
# Security scanning (if enabled)
# See snyk_rules.instructions.md for details
```

## Architecture Stability Rules

- **Never** change module responsibilities without updating system_index.yaml first
- **Never** add dependencies without documenting in system_index.yaml.dependencies
- **Never** bypass Policy Guardian in code — it's a hard constraint, not a suggestion
- **Never** modify audit.py without understanding append-only semantics
- **Always** preserve backward compatibility with existing schemas in /schemas

## Questions?

- System structure/responsibilities → Check `system_index.yaml`
- Data model details → Check `DATA_MODEL.md` and `/schemas`
- Policy/permissions → Check `POLICIES.md` and `AGENTS.md`
- Implementation priorities → Check `MILESTONES.md`
- Design rationale → Check `docs/decision-log.md`
