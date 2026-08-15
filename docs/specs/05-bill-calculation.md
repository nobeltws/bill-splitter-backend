# Feature 5: Bill Calculation

## Scope

Calculate each participant's total share including their proportional portion of tax, service charge, and discount.

## What This Includes

- Calculation service that computes per-participant totals
- Proportional distribution of tax/service charge/discount based on each participant's item subtotal relative to the overall subtotal
- Summary endpoint
- Python `Decimal` type for precise arithmetic (no floating point errors)

## Formula

```
participant_subtotal = sum of (claimed_quantity / item_quantity * item_total_price) for each claimed item
raw_subtotal = sum of (quantity * unit_price) for all items

participant_share = participant_subtotal * (1 + (tax + service_charge - discount) / raw_subtotal)
```

All arithmetic uses `decimal.Decimal` with `ROUND_HALF_EVEN` (banker's rounding).

## API

```
GET /api/sessions/:id/summary

Response 200:
{
  "rawSubtotal": 50.00,
  "tax": 3.50,
  "serviceCharge": 5.00,
  "discount": 0,
  "grandTotal": 58.50,
  "participants": [
    {
      "name": "Alice",
      "itemsSubtotal": 20.00,
      "proportionalTax": 1.40,
      "proportionalServiceCharge": 2.00,
      "proportionalDiscount": 0,
      "totalOwed": 23.40
    }
  ],
  "unclaimed": {
    "items": [...],
    "subtotal": 10.00
  }
}
```

## Edge Cases

- Items with no claims: reported as "unclaimed" in the summary
- Rounding: use banker's rounding (`ROUND_HALF_EVEN`); if amounts don't sum to grand total due to rounding, adjust the largest share
- Zero subtotal: return 0 for all proportional values
- Discount exceeds subtotal: cap effective adjustment at 0 (no negative shares)

## Out of Scope

- Historical calculation snapshots
- Per-item tax rates (single tax rate for the whole bill)
- Tip calculation

## Acceptance Criteria

- Participant shares sum to the grand total (accounting for rounding)
- Tax/service charge/discount are distributed proportionally
- Unclaimed items are clearly reported
- Participants with no claims show a total of 0
- Endpoint returns 404 for invalid session ID
- All monetary calculations use `Decimal` — no floating point
