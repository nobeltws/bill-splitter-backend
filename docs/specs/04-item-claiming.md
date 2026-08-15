# Feature 4: Item Claiming

## Scope

Allow participants to claim items from the session. An item can be claimed by multiple participants (shared), and the total claimed quantity cannot exceed the item's available quantity.

## What This Includes

- Claim items endpoint (participant identifies themselves by name)
- Support for shared items (multiple people claim the same item)
- Quantity validation (can't over-claim)
- Claims visible to all participants via the session GET endpoint
- Database table: claims

## API

```
POST /api/sessions/:id/claims
Body:
{
  "participantName": "Alice",
  "claims": [
    { "itemId": "uuid", "quantity": 1 }
  ]
}

Response 200:
{
  "participantName": "Alice",
  "claims": [
    { "itemId": "uuid", "itemName": "Chicken Rice", "quantity": 1 }
  ]
}
```

```
DELETE /api/sessions/:id/claims
Body:
{
  "participantName": "Alice",
  "itemId": "uuid"
}

Response 200: { "message": "Claim removed" }
```

## Database

```sql
CREATE TABLE claims (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  item_id UUID REFERENCES items(id) ON DELETE CASCADE,
  participant_name VARCHAR(100) NOT NULL,
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  UNIQUE(session_id, item_id, participant_name)
);
```

## Validation Rules

- Sum of all claims on an item cannot exceed the item's quantity
- Participant name must be non-empty
- Quantity must be > 0
- Item must belong to the specified session

## Out of Scope

- Participant identity management (they self-identify by name)
- Real-time notifications of claim changes
- Locking/conflict resolution (last write wins for v1)

## Acceptance Criteria

- A participant can claim one or more items
- Multiple participants can claim the same item (shared)
- Over-claiming returns 400 with a clear error
- Claims appear in the session GET response
- A participant can remove their claim on an item
- Claiming with a quantity of 0 or negative returns 422 (Pydantic validation)
