# Bill Splitter Backend

Upload a photo of your receipt and split the bill with your friends.

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** FastAPI (async)
- **Database:** PostgreSQL with SQLAlchemy 2.0 (async) + Alembic
- **OCR:** docTR (PyTorch backend, CPU inference)
- **Validation:** Pydantic v2
- **Architecture:** Router → Service → Repository

## Prerequisites

- Python 3.11+
- PostgreSQL running locally (or via Docker)

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -e ".[dev]"
```

3. Create your environment file:

```bash
cp .env.example .env
```

4. Update `.env` with your database credentials:

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/billsplitter
HOST=0.0.0.0
PORT=8000
```

5. Create the database and run migrations:

```bash
createdb billsplitter
alembic upgrade head
```

## Running

### Development (with hot reload)

```bash
uvicorn app.main:app --reload
```

### Docker (recommended)

```bash
docker compose up --build
```

This starts both PostgreSQL and the API server. Migrations run automatically on startup.

## Scripts

| Command | Description |
|---------|-------------|
| `uvicorn app.main:app --reload` | Start dev server with hot reload |
| `pytest` | Run all tests |
| `pytest -v` | Run tests with verbose output |
| `ruff check .` | Lint code |
| `ruff format .` | Format code |
| `alembic upgrade head` | Run pending migrations |
| `alembic revision --autogenerate -m "msg"` | Generate migration from model changes |
| `alembic downgrade -1` | Revert last migration |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/receipts/parse` | OCR + parse a receipt image |
| POST | `/api/sessions` | Create a bill-splitting session |
| GET | `/api/sessions/:id` | Get session state |
| POST | `/api/sessions/:id/claims` | Claim items |
| DELETE | `/api/sessions/:id/claims` | Remove a claim |
| GET | `/api/sessions/:id/summary` | Get calculated bill split |
| POST | `/api/sessions/:id/payments` | Mark as paid |
| DELETE | `/api/sessions/:id/payments` | Unmark payment |

Interactive API docs available at `http://localhost:8000/docs` (Swagger UI).

## Project Structure

```
app/
├── main.py              # FastAPI app factory, lifespan events
├── config.py            # Settings (pydantic-settings, reads .env)
├── database.py          # Async SQLAlchemy engine + session factory
├── exceptions.py        # JSON exception handlers (404, 500)
├── api/                 # Route handlers (thin, delegate to services)
│   ├── health.py
│   ├── receipts.py
│   ├── sessions.py
│   ├── claims.py
│   └── payments.py
├── services/            # Business logic
│   ├── ocr.py           # docTR model wrapper
│   ├── receipt_parser.py
│   ├── session.py
│   ├── claim.py
│   ├── calculation.py
│   └── payment.py
├── models/              # SQLAlchemy table models
├── schemas/             # Pydantic request/response schemas
└── repositories/        # Database queries
alembic/                 # Migration files
tests/                   # pytest test suite
```

## Error Responses

All errors return consistent JSON:

```json
{ "detail": "Error message here" }
```

- **404** — Unknown routes: `{ "detail": "Not Found" }`
- **422** — Validation errors: Pydantic error details
- **400** — Business rule violations (e.g., over-claiming)
- **500** — Unhandled errors: `{ "detail": "Internal Server Error" }`
