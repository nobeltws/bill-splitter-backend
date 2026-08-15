# Feature 3: Session Management

## Scope

Allow the host to create a session with their finalized item list and PayNow details. Provide a shareable session ID for participants to fetch the bill state.

## What This Includes

- Create session endpoint (accepts finalized items + host PayNow ID)
- Get session endpoint (returns full session state for participants)
- UUID-based session IDs (shareable, unguessable)
- Database tables: sessions, items
- Input validation via Pydantic models (items must have name, quantity > 0, unitPrice > 0)

## API

```
POST /api/sessions
Body:
{
  "hostPaynowId": "+6591234567",
  "items": [
    { "name": "Chicken Rice", "quantity": 2, "unitPrice": 6.50 }
  ],
  "tax": 1.20,
  "serviceCharge": 2.00,
  "discount": 0
}

Response 201:
{
  "sessionId": "uuid-here",
  "createdAt": "..."
}
```

```
GET /api/sessions/:id

Response 200:
{
  "sessionId": "uuid-here",
  "hostPaynowId": "+6591234567",
  "items": [...],
  "tax": 1.20,
  "serviceCharge": 2.00,
  "discount": 0,
  "claims": [],
  "payments": [],
  "createdAt": "..."
}
```

## Database

```sql
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  host_paynow_id VARCHAR(50) NOT NULL,
  tax DECIMAL(10,2) DEFAULT 0,
  service_charge DECIMAL(10,2) DEFAULT 0,
  discount DECIMAL(10,2) DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price > 0)
);
```

## SQLAlchemy Models

```python
class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    host_paynow_id: Mapped[str] = mapped_column(String(50))
    tax: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    service_charge: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    discount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    items: Mapped[list["Item"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    claims: Mapped[list["Claim"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="session", cascade="all, delete-orphan")
```

## Out of Scope

- Editing sessions after creation
- Session expiry/cleanup (future concern)
- Authentication of the host

## Acceptance Criteria

- Host can create a session with items and PayNow ID
- Session ID is a UUID returned on creation
- Participants can fetch full session state by ID
- Invalid session ID returns 404
- Missing/invalid fields return 422 with Pydantic validation errors
