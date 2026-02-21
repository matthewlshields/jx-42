# Investing Strategy Example

This document illustrates an end-to-end example of the Investing Program Agent processing a portfolio review and generating trade proposals.

## User Input

> "Review my portfolio and suggest rebalancing trades to bring it in line with my target allocation."

## User's Stated Strategy

- **Risk profile**: Moderate
- **Investment horizon**: 10 years
- **Target allocation**:
  - 60% US equities (broad market)
  - 20% International equities
  - 15% Bonds
  - 5% Cash

## Current Holdings (as of 2026-03-31)

| Symbol | Asset Class | Qty   | Price (USD) | Market Value (USD) | % of Portfolio |
|--------|-------------|-------|-------------|--------------------|----------------|
| VTI    | ETF         | 50    | 240.00      | 12,000.00          | 68.2%          |
| VXUS   | ETF         | 20    | 65.00       | 1,300.00           | 7.4%           |
| BND    | ETF         | 15    | 75.00       | 1,125.00           | 6.4%           |
| CASH   | Cash        | —     | —           | 3,150.00           | 17.9%          |
| **Total** |          |       |             | **17,575.00**      | **100%**       |

## Gap Analysis

| Asset Class          | Target % | Current % | Gap      | Action Needed        |
|----------------------|----------|-----------|----------|----------------------|
| US equities (VTI)    | 60%      | 68.2%     | -8.2%    | Trim / sell          |
| International (VXUS) | 20%      | 7.4%      | +12.6%   | Buy                  |
| Bonds (BND)          | 15%      | 6.4%      | +8.6%    | Buy                  |
| Cash                 | 5%       | 17.9%     | -12.9%   | Deploy               |

## Proposed Trade Tickets

### Ticket 1 — Sell VTI

```json
{
  "ticket_id": "b2c3d4e5-0001-0000-0000-000000000001",
  "symbol": "VTI",
  "asset_class": "etf",
  "action": "sell",
  "quantity": 6,
  "limit_price": 240.00,
  "currency": "USD",
  "rationale": "Portfolio is 8.2% over-weight in US equities relative to the 60% target. Selling 6 shares of VTI at the current price raises approximately $1,440 to redeploy into under-weight positions.",
  "status": "proposed",
  "created_at": "2026-03-31T09:00:00Z"
}
```

### Ticket 2 — Buy VXUS

```json
{
  "ticket_id": "b2c3d4e5-0001-0000-0000-000000000002",
  "symbol": "VXUS",
  "asset_class": "etf",
  "action": "buy",
  "quantity": 22,
  "limit_price": 65.00,
  "currency": "USD",
  "rationale": "International equities are 12.6% below target allocation. Buying 22 shares of VXUS adds $1,430 of international equity exposure, bringing the allocation closer to the 20% target.",
  "status": "proposed",
  "created_at": "2026-03-31T09:00:00Z"
}
```

### Ticket 3 — Buy BND

```json
{
  "ticket_id": "b2c3d4e5-0001-0000-0000-000000000003",
  "symbol": "BND",
  "asset_class": "bond",
  "action": "buy",
  "quantity": 20,
  "limit_price": 75.00,
  "currency": "USD",
  "rationale": "Bond allocation is 8.6% below target. Buying 20 shares of BND adds $1,500 of fixed-income exposure. This reduces portfolio volatility in line with the moderate risk profile.",
  "status": "proposed",
  "created_at": "2026-03-31T09:00:00Z"
}
```

## Post-Rebalance Projection

| Symbol | Asset Class | Qty | Market Value (USD) | % of Portfolio |
|--------|-------------|-----|--------------------|----------------|
| VTI    | ETF         | 44  | 10,560.00          | 60.1%          |
| VXUS   | ETF         | 42  | 2,730.00           | 15.5%          |
| BND    | ETF         | 35  | 2,625.00           | 14.9%          |
| CASH   | Cash        | —   | 1,660.00           | 9.4%           |
| **Total** |          |     | **17,575.00**      | **100%**       |

> ⚠️ **Data note**: Cash allocation will remain above target (9.4% vs 5%) after this rebalance. A follow-up rebalance is recommended once additional investment funds are available.

## Risk Flags

- No single trade exceeds 20% of portfolio value. ✅
- No leveraged or derivative instruments proposed. ✅
- Trades are consistent with a moderate 10-year investment horizon. ✅

## Policy Guardian Verdict

```json
{
  "verdict": "approved",
  "policy_flags": ["P-01", "P-02", "P-05"],
  "reason": null
}
```

*Note: P-01 requires human confirmation before any trade is submitted to a brokerage. These tickets remain in `proposed` status until the user explicitly approves.*
