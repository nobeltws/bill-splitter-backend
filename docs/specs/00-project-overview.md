# Bill Splitter Backend — Project Overview

## Summary

A receipt-splitting backend API built with FastAPI + Python using the router/service/repository pattern with PostgreSQL.

Users upload a receipt photo, the backend extracts text via docTR and parses it into structured items using regex heuristics with spatial awareness, then the host creates a shareable session. Participants join via link (no accounts), claim items, and see their calculated share including proportional tax/service charge. Payment is tracked via PayNow.

## Key Decisions

- **Framework:** FastAPI (async, auto-generated OpenAPI docs)
- **Architecture:** Router → Service → Repository
- **Database:** PostgreSQL with SQLAlchemy 2.0 (async) + Alembic migrations
- **OCR:** docTR (PyTorch backend, CPU inference)
- **Parsing:** Regex heuristics with bounding-box spatial awareness
- **Validation:** Pydantic v2
- **Auth:** None — anonymous, link-based sessions
- **Real-time:** Polling/refresh for v1 (no WebSockets)
- **Item editing:** Host edits locally on frontend, submits finalized list once
- **Payments:** Backend stores host's PayNow ID; participants generate QR client-side

## Feature Specs (Build Order)

1. [Project Foundation](./01-project-foundation.md)
2. [Receipt OCR & Parsing](./02-receipt-ocr-parsing.md)
3. [Session Management](./03-session-management.md)
4. [Item Claiming](./04-item-claiming.md)
5. [Bill Calculation](./05-bill-calculation.md)
6. [Payment Status](./06-payment-status.md)

## Data Model (High-Level)

```
Session
├── id (UUID, shareable)
├── host_paynow_id (string)
├── tax (decimal)
├── service_charge (decimal)
├── discount (decimal)
├── created_at
│
├── Items[]
│   ├── id
│   ├── name
│   ├── quantity
│   ├── unit_price
│   │
│   └── Claims[]
│       ├── participant_name
│       └── quantity_claimed
│
└── Payments[]
    ├── participant_name
    └── paid (boolean)
```

## Project Structure

```
bill-splitter-backend/
├── app/
│   ├── main.py              # FastAPI app factory, lifespan events
│   ├── config.py            # Settings from env vars (pydantic-settings)
│   ├── database.py          # SQLAlchemy async engine + session factory
│   ├── models/              # SQLAlchemy table models
│   │   ├── session.py
│   │   ├── item.py
│   │   ├── claim.py
│   │   └── payment.py
│   ├── schemas/             # Pydantic request/response schemas
│   │   ├── receipt.py
│   │   ├── session.py
│   │   ├── claim.py
│   │   └── payment.py
│   ├── api/                 # Route handlers (thin, delegate to services)
│   │   ├── health.py
│   │   ├── receipts.py
│   │   ├── sessions.py
│   │   ├── claims.py
│   │   └── payments.py
│   ├── services/            # Business logic
│   │   ├── receipt_parser.py
│   │   ├── ocr.py
│   │   ├── session.py
│   │   ├── claim.py
│   │   ├── calculation.py
│   │   └── payment.py
│   └── repositories/        # DB queries
│       ├── session.py
│       ├── item.py
│       ├── claim.py
│       └── payment.py
├── alembic/                 # Database migrations
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```
