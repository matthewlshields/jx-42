# JX-42 Policies (v1)

## 1 Permission Tiers
- Read-only: fetch/summarize/propose
- Draft-only: create drafts (emails/events/plans/trade tickets)
- Execute-with-confirm: requires explicit approval per action
- Auto-execute: only for low-risk, explicitly whitelisted routines (not enabled v1)

## 2 Global Rules
- No external tool call without Policy Guardian approval.
- Unknown connector/tool is denied by default.
- Every step must produce an audit event.

## 3 Finance Rules (v1)
- No transfers, bill-pay changes, autopay changes, or new payees.
- Reports and drafts allowed.
- Any instruction phrased as “move money / pay / transfer” => blocked with guidance.

## 4 Investing Rules (v1)
- No live order placement.
- Draft trade tickets allowed.
- Paper trading is recommended before enabling execution in future.
- Risk limits must be defined before generating tickets:
  - max position size
  - max daily/weekly risk budget
  - max drawdown kill-switch threshold

## 5 Confirmation Policy (reserved for v2)
- Single confirm: medium-risk actions
- Double confirm: high-risk actions (large dollar amounts, new destinations)
- Cooldown timers after large losses or large transfers