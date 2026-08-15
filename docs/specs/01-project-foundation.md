# Feature 1: Project Foundation

## Scope

Scaffold the KOA + TypeScript project with the controller/service/repo architecture, PostgreSQL connection, and baseline middleware.

## What This Includes

- TypeScript + KOA project setup (tsconfig, scripts, dev/build tooling)
- Folder structure: `src/controllers/`, `src/services/`, `src/repos/`, `src/middleware/`, `src/config/`
- PostgreSQL connection setup (TypeORM DataSource, config from env vars)
- Database migration tooling (TypeORM migrations)
- Error handling middleware (consistent JSON error responses)
- Request logging middleware
- CORS configuration
- Health check endpoint: `GET /health`
- Environment config management (dotenv or similar)

## API

```
GET /health → { status: "ok" }
```

## Out of Scope

- Any business logic
- Authentication/authorization
- Specific database tables (those come with each feature)

## Acceptance Criteria

- `npm run dev` starts the server with hot reload
- `npm run build` produces a production build
- `GET /health` returns 200
- PostgreSQL connection is verified on startup
- Invalid routes return a consistent 404 JSON response
- Unhandled errors return a consistent 500 JSON response
