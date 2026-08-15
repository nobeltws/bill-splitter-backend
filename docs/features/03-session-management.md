# Feature 3: Session Management

## Summary

Allows the host to create a bill-splitting session with finalized items and PayNow ID, and lets participants fetch the full session state via a shareable UUID link.

## What Was Built

### Endpoints

#### Create Session

```
POST /api/sessions
Content-Type: application/json

{
  "hostPaynowId": "+6591234567",
  "items": [
    { "name": "Chicken Rice", "quantity": 2, "unitPrice": 6.50 },
    { "name": "Laksa", "quantity": 1, "unitPrice": 8.50 }
  ],
  "tax": 1.20,
  "serviceCharge": 2.00,
  "discount": 0
}
```

**Response 201:**
```json
{
  "sessionId": "uuid-v4",
  "createdAt": "2026-08-15T10:30:00.000Z"
}
```

#### Get Session

```
GET /api/sessions/:id
```

**Response 200:**
```json
{
  "sessionId": "uuid-v4",
  "hostPaynowId": "+6591234567",
  "items": [
    { "id": "uuid", "name": "Chicken Rice", "quantity": 2, "unitPrice": 6.50 }
  ],
  "tax": 1.20,
  "serviceCharge": 2.00,
  "discount": 0,
  "claims": [],
  "payments": [],
  "createdAt": "2026-08-15T10:30:00.000Z"
}
```

### Validation (POST /api/sessions)

| Condition | Response |
|-----------|----------|
| Missing/empty hostPaynowId | 400 — `hostPaynowId is required` |
| Empty items array | 400 — `At least one item is required in items` |
| Item with empty name | 400 — `Item N: name is required` |
| Item with quantity <= 0 | 400 — `Item N: quantity must be greater than 0` |
| Item with unitPrice <= 0 | 400 — `Item N: unitPrice must be greater than 0` |
| Negative tax | 400 — `tax cannot be negative` |
| Negative serviceCharge | 400 — `serviceCharge cannot be negative` |
| Negative discount | 400 — `discount cannot be negative` |
| Non-existent session ID | 404 — `Session not found` |

### Components

| File | Responsibility |
|------|---------------|
| `src/entities/session.entity.ts` | Session TypeORM entity (UUID PK, hostPaynowId, tax, serviceCharge, discount, createdAt, items relation) |
| `src/entities/item.entity.ts` | Item TypeORM entity (UUID PK, name, quantity, unitPrice, session relation) |
| `migrations/1723680000000-CreateSessionAndItemTables.ts` | Creates sessions and items tables with constraints |
| `src/repos/session.repo.ts` | Database access — createSession (with cascading items), findSessionById |
| `src/services/session.service.ts` | Input validation logic (validateCreateSessionInput) |
| `src/controllers/session.controller.ts` | HTTP handlers — createSessionHandler, getSessionHandler |

### Database Schema

**sessions table:**
- `id` UUID PRIMARY KEY (auto-generated)
- `host_paynow_id` VARCHAR(50) NOT NULL
- `tax` DECIMAL(10,2) DEFAULT 0
- `service_charge` DECIMAL(10,2) DEFAULT 0
- `discount` DECIMAL(10,2) DEFAULT 0
- `created_at` TIMESTAMP DEFAULT NOW()

**items table:**
- `id` UUID PRIMARY KEY (auto-generated)
- `session_id` UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE
- `name` VARCHAR(255) NOT NULL
- `quantity` INTEGER NOT NULL CHECK (quantity > 0)
- `unit_price` DECIMAL(10,2) NOT NULL CHECK (unit_price > 0)

### Docker Support

Added `Dockerfile` and `docker-compose.yml` for containerized deployment:
- **db** service: PostgreSQL 16 Alpine with healthcheck
- **server** service: Node.js app, depends on healthy db

## Testing

- 29 tests total across 6 suites
- Run with `npm test`

### Unit Tests (9 tests)
- `tests/unit/services/session.service.test.ts`
  - Returns null for valid input
  - Error when hostPaynowId missing
  - Error when items array empty
  - Error when item name empty
  - Error when item quantity is 0 or negative
  - Error when item unitPrice is 0 or negative
  - Error when tax negative
  - Error when serviceCharge negative
  - Error when discount negative

### Integration Tests (6 tests)
- `tests/integration/session.test.ts`
  - Creates session and returns 201 with UUID sessionId
  - Returns 400 when hostPaynowId missing
  - Returns 400 when items empty
  - Returns 400 when item has invalid quantity
  - Returns 200 with full session state
  - Returns 404 for non-existent session

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| UUID primary keys | Shareable links without exposing sequential IDs |
| Cascading item creation | Single atomic write for session + items |
| `claims: []` and `payments: []` in GET response | Prepares response shape for Features 4 and 6 |
| Database CHECK constraints | Enforces data integrity at DB level (quantity > 0, unit_price > 0) |
| Decimal types for money fields | Avoids floating-point precision issues |
| Number() cast in GET response | TypeORM returns decimal columns as strings; cast for JSON response |

## Running Locally

```bash
# Start PostgreSQL
docker-compose up -d db

# Run migrations
npm run migration:run

# Start server
npm run dev

# Run tests (requires running PostgreSQL)
npm test
```
