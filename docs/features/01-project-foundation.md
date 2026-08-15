# Feature 1: Project Foundation

## Summary

Scaffolded the KOA + TypeScript backend with a layered architecture (controller → service → repository), TypeORM for PostgreSQL, and baseline middleware.

## What Was Built

### Server Infrastructure
- **KOA application** (`src/app.ts`) — composes middleware stack and mounts routes
- **Server entry point** (`src/server.ts`) — initializes TypeORM, then starts listening
- **Config module** (`src/config/index.ts`) — reads environment variables via dotenv

### Database
- **TypeORM DataSource** (`src/db/data-source.ts`) — PostgreSQL connection with migration support
- Migration scripts configured via `npm run migration:*`

### Middleware (applied in order)
1. **errorHandler** — catches thrown errors, returns consistent JSON `{ error: "..." }`
2. **requestLogger** — logs `METHOD /path STATUS durationMs`
3. **CORS** — via `@koa/cors` with default config
4. **Router** — mounted routes
5. **notFound** — returns 404 JSON for unmatched routes

### Endpoints
| Method | Path | Response |
|--------|------|----------|
| GET | `/health` | `{ status: "ok" }` |

### Folder Structure
| Directory | Purpose |
|-----------|---------|
| `src/controllers/` | Route handlers |
| `src/services/` | Business logic |
| `src/repos/` | Database access (TypeORM repositories) |
| `src/entities/` | TypeORM entity classes |
| `src/middleware/` | KOA middleware |
| `src/routes/` | Route definitions |
| `src/config/` | Environment config |
| `src/db/` | Database connection |
| `migrations/` | TypeORM migration files |

## Testing

- 4 tests total (2 unit, 2 integration)
- Run with `npm test`

### Unit Tests
- `tests/unit/middleware/errorHandler.test.ts` — verifies 500 for unhandled errors, custom status codes for errors with `.status`

### Integration Tests
- `tests/integration/health.test.ts` — verifies `GET /health` returns 200, unknown routes return 404

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| TypeORM over Knex | Provides ORM + migrations + repository pattern out of the box |
| `tsx watch` for dev | Fast TypeScript execution without separate compile step |
| `synchronize: false` | Migrations-only approach for safe production deployments |
| Middleware order: errorHandler first | Catches errors from all downstream middleware |
| notFound last | Only triggers if no route matched and no body was set |
