# Architecture

## Overview

Bill Splitter is a monolith FastAPI application using the **Router → Service → Repository** pattern with async PostgreSQL via SQLAlchemy 2.0.

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI App                        │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  Routers │→ │ Services │→ │  Repositories    │  │
│  │  (API)   │  │ (Logic)  │  │  (DB Queries)    │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│       ↑              ↑              ↑               │
│  Pydantic       Business        SQLAlchemy          │
│  Schemas        Rules           Models              │
└─────────────────────────────────────────────────────┘
         ↕                              ↕
    HTTP Clients                   PostgreSQL
```

## Layers

### Routers (`app/api/`)

Thin HTTP handlers. Responsibilities:
- Accept and validate requests (via Pydantic schemas)
- Call the appropriate service
- Return responses

Routers do NOT contain business logic or database queries.

### Services (`app/services/`)

Business logic layer. Responsibilities:
- Implement domain rules (e.g., "can't over-claim an item")
- Orchestrate multiple repository calls
- Raise HTTP exceptions for business rule violations

Services are injected with DB sessions via FastAPI's `Depends()`.

### Repositories (`app/repositories/`)

Data access layer. Responsibilities:
- Execute SQLAlchemy queries
- Return model instances or None
- No business logic — just CRUD operations

### Models (`app/models/`)

SQLAlchemy 2.0 mapped classes representing database tables.

### Schemas (`app/schemas/`)

Pydantic v2 models for request/response validation and serialization.

## Key Patterns

### Dependency Injection

FastAPI's `Depends()` is used for:
- DB session per request (`get_session`)
- Service instances (if needed)
- Shared resources (OCR model)

### Async All the Way

- Async SQLAlchemy with `asyncpg` driver
- Async FastAPI route handlers
- Async lifespan events (DB check on startup)

### OCR Pipeline

```
Image Upload → docTR (text extraction) → Spatial Line Reconstruction → Regex Parser → Structured JSON
```

The docTR model is loaded once at app startup via the lifespan context manager. It stays in memory for the lifetime of the process.

### Database Migrations

Alembic with async support. Migrations run automatically in Docker (`alembic upgrade head` before server start).

## Data Flow

### Receipt Parsing (stateless)

```
Client → POST /api/receipts/parse (image)
       → OCR Service (docTR inference)
       → Receipt Parser (regex heuristics)
       → Response: { items, tax, serviceCharge }
```

### Bill Splitting (stateful)

```
1. Host creates session:     POST /api/sessions → sessionId
2. Participants view:        GET /api/sessions/:id
3. Participants claim:       POST /api/sessions/:id/claims
4. View split:               GET /api/sessions/:id/summary
5. Mark paid:                POST /api/sessions/:id/payments
```

## Configuration

All config via environment variables, loaded by `pydantic-settings`:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string (must use `postgresql+asyncpg://`) | required |
| `HOST` | Server bind address | `0.0.0.0` |
| `PORT` | Server port | `8000` |
