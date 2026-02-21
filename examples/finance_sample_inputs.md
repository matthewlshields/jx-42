# Finance Sample Inputs

Sample `FinanceLedger` entries for testing the Finance Program Agent.

## Sample Dataset: March 2026

```json
[
  {
    "entry_id": "a1b2c3d4-0001-0000-0000-000000000001",
    "account_id": "acct-ref-001",
    "date": "2026-03-01",
    "description": "Opening balance",
    "amount": 0.00,
    "currency": "USD",
    "category": "balance",
    "running_balance": 4250.00
  },
  {
    "entry_id": "a1b2c3d4-0001-0000-0000-000000000002",
    "account_id": "acct-ref-001",
    "date": "2026-03-03",
    "description": "Employer payroll deposit",
    "amount": 3800.00,
    "currency": "USD",
    "category": "salary",
    "running_balance": 8050.00,
    "tags": ["income", "regular"]
  },
  {
    "entry_id": "a1b2c3d4-0001-0000-0000-000000000003",
    "account_id": "acct-ref-001",
    "date": "2026-03-05",
    "description": "Rent payment",
    "amount": -1500.00,
    "currency": "USD",
    "category": "housing",
    "running_balance": 6550.00,
    "tags": ["fixed", "monthly"]
  },
  {
    "entry_id": "a1b2c3d4-0001-0000-0000-000000000004",
    "account_id": "acct-ref-001",
    "date": "2026-03-07",
    "description": "Grocery store",
    "amount": -112.45,
    "currency": "USD",
    "category": "groceries",
    "running_balance": 6437.55
  },
  {
    "entry_id": "a1b2c3d4-0001-0000-0000-000000000005",
    "account_id": "acct-ref-001",
    "date": "2026-03-10",
    "description": "Electric utility bill",
    "amount": -87.00,
    "currency": "USD",
    "category": "utilities",
    "running_balance": 6350.55,
    "tags": ["fixed", "monthly"]
  },
  {
    "entry_id": "a1b2c3d4-0001-0000-0000-000000000006",
    "account_id": "acct-ref-001",
    "date": "2026-03-12",
    "description": "Streaming subscriptions",
    "amount": -32.97,
    "currency": "USD",
    "category": "entertainment",
    "running_balance": 6317.58,
    "tags": ["subscription"]
  },
  {
    "entry_id": "a1b2c3d4-0001-0000-0000-000000000007",
    "account_id": "acct-ref-001",
    "date": "2026-03-14",
    "description": "Grocery store",
    "amount": -94.20,
    "currency": "USD",
    "category": "groceries",
    "running_balance": 6223.38
  },
  {
    "entry_id": "a1b2c3d4-0001-0000-0000-000000000008",
    "account_id": "acct-ref-001",
    "date": "2026-03-18",
    "description": "Restaurant dinner",
    "amount": -67.50,
    "currency": "USD",
    "category": "dining",
    "running_balance": 6155.88
  },
  {
    "entry_id": "a1b2c3d4-0001-0000-0000-000000000009",
    "account_id": "acct-ref-001",
    "date": "2026-03-20",
    "description": "Transfer to savings account",
    "amount": -500.00,
    "currency": "USD",
    "category": "savings",
    "running_balance": 5655.88,
    "tags": ["transfer", "savings"]
  },
  {
    "entry_id": "a1b2c3d4-0001-0000-0000-000000000010",
    "account_id": "acct-ref-001",
    "date": "2026-03-25",
    "description": "Petrol / fuel",
    "amount": -58.00,
    "currency": "USD",
    "category": "transport",
    "running_balance": 5597.88
  },
  {
    "entry_id": "a1b2c3d4-0001-0000-0000-000000000011",
    "account_id": "acct-ref-001",
    "date": "2026-03-28",
    "description": "Grocery store",
    "amount": -105.10,
    "currency": "USD",
    "category": "groceries",
    "running_balance": 5492.78
  },
  {
    "entry_id": "a1b2c3d4-0001-0000-0000-000000000012",
    "account_id": "acct-ref-001",
    "date": "2026-03-31",
    "description": "Internet service provider",
    "amount": -59.99,
    "currency": "USD",
    "category": "utilities",
    "running_balance": 5432.79,
    "tags": ["fixed", "monthly"]
  }
]
```

## Expected Analysis Output

When the Finance Program Agent processes the above dataset, the expected output should include:

| Category      | Total (USD) | % of Expenses |
|---------------|-------------|---------------|
| Housing       | 1,500.00    | 55.3%         |
| Groceries     | 311.75      | 11.5%         |
| Savings       | 500.00      | 18.4%         |
| Utilities     | 146.99      | 5.4%          |
| Dining        | 67.50       | 2.5%          |
| Transport     | 58.00       | 2.1%          |
| Entertainment | 32.97       | 1.2%          |

- **Total Income**: $3,800.00
- **Total Expenses**: $2,714.71 (excluding savings transfer)
- **Net (after savings)**: $1,085.29
- **Closing Balance**: $5,432.79

### Insight Examples
- Groceries account for 3 separate transactions totalling $311.75 — potential to consolidate shopping trips.
- Savings transfer of $500.00 executed on schedule (20th of month).
- No unusual or anomalous transactions detected.
