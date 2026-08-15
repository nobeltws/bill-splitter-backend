# Feature 1: Project Foundation

## Scope

Scaffold the FastAPI + Python project with the router/service/repository architecture, async PostgreSQL connection, and baseline middleware.

## What This Includes

- Python project setup with `pyproject.toml` (dependencies, scripts, metadata)
- Folder structure: `app/api/`, `app/services/`, `app/repositories/`, `app/models/`, `app/schemas/`
- FastAPI app factory with lifespan events (startup/shutdown)
- Async SQLAlchemy 2.0 engine + session factory, config from env vars
- Alembic migration tooling (async driver: asyncpg)
- Exception handlers (consistent JSON error responses via FastAPI exception handlers)
- Request logging middleware (timing + method/path)
- CORS configuration
- Health check endpoint: `GET /health`
- Environment config via pydantic-settings (reads from `.env`)
- Dev tooling: Ruff (linting + formatting), pytest, uvicorn (dev server with reload)

## Dependencies

```
# Core
fastapi
uvicorn[standard]
pydantic-settings
sqlalchemy[asyncio]
asyncpg
alembic

# OCR (installed here, used in Feature 2)
python-doctr[torch]
torch (CPU-only)

# Dev
pytest
pytest-asyncio
httpx (for async test client)
ruff
```

## API

```
GET /health → { "status": "ok" }
```

## Out of Scope

- Any business logic
- Authentication/authorization
- Specific database tables (those come with each feature)

## Acceptance Criteria

- `uvicorn app.main:app --reload` starts the server with hot reload
- `GET /health` returns 200
- PostgreSQL connection is verified on startup (lifespan event)
- Auto-generated OpenAPI docs available at `/docs`
- Invalid routes return a consistent 404 JSON response
- Unhandled errors return a consistent 500 JSON response
- `ruff check` passes with no errors
- `pytest` runs (even if no tests yet)
