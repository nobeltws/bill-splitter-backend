# Feature 6: Payment Status

## Scope

Allow participants to mark themselves as having paid. The host and other participants can see who has and hasn't paid.

## What This Includes

- Mark as paid endpoint
- Payment status visible in session GET response
- Database table: payments

## API

```
POST /api/sessions/:id/payments
Body:
{
  "participantName": "Alice"
}

Response 200:
{
  "participantName": "Alice",
  "paid": true,
  "paidAt": "2024-01-15T10:30:00Z"
}
```

```
DELETE /api/sessions/:id/payments
Body:
{
  "participantName": "Alice"
}

Response 200:
{
  "participantName": "Alice",
  "paid": false
}
```

## Database

```sql
CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  participant_name VARCHAR(100) NOT NULL,
  paid_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(session_id, participant_name)
);
```

## Validation Rules

- Participant must have at least one claim in the session to mark as paid
- Cannot mark as paid twice (idempotent — return existing status)
- Participant name must match an existing claimant

## Out of Scope

- Actual payment verification (no bank API integration)
- Host-initiated payment marking
- Payment reminders/notifications
- Payment amounts (we trust participants to pay the correct amount)

## Acceptance Criteria

- A participant with claims can mark themselves as paid
- Payment status appears in the session GET response
- Marking as paid is idempotent
- A participant can unmark their payment
- A participant with no claims cannot mark as paid (returns 400)
- Payment timestamp is recorded
