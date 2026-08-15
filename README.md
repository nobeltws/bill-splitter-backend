# Bill Splitter Backend

Upload a photo of your receipt and split the bill with your friends.

## Tech Stack

- **Runtime:** Node.js + TypeScript
- **Framework:** KOA
- **Database:** PostgreSQL
- **ORM:** TypeORM
- **Architecture:** Controller → Service → Repository

## Prerequisites

- Node.js >= 18
- PostgreSQL running locally (or a remote connection URL)

## Setup

1. Install dependencies:

```bash
npm install
```

2. Create your environment file:

```bash
cp .env.example .env
```

3. Update `.env` with your database credentials:

```
PORT=3000
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/bill_splitter
NODE_ENV=development
```

4. Create the database:

```bash
createdb bill_splitter
```

5. Run migrations (when migrations exist):

```bash
npm run migration:run
```

## Running

### Development (with hot reload)

```bash
npm run dev
```

### Production

```bash
npm run build
npm start
```

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server with hot reload |
| `npm run build` | Compile TypeScript to `dist/` |
| `npm start` | Run compiled production build |
| `npm test` | Run all tests |
| `npm run test:watch` | Run tests in watch mode |
| `npm run migration:run` | Run pending migrations |
| `npm run migration:generate` | Generate migration from entity changes |
| `npm run migration:revert` | Revert last migration |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check — returns `{ status: "ok" }` |

## Project Structure

```
src/
├── app.ts                  # KOA app (middleware + router)
├── server.ts               # Entry point (DB init + listen)
├── config/                 # Environment configuration
├── controllers/            # Route handlers
├── services/               # Business logic
├── repos/                  # Database access
├── entities/               # TypeORM entity classes
├── middleware/             # KOA middleware
│   ├── errorHandler.ts     # Catches errors → JSON response
│   ├── notFound.ts         # 404 handler
│   └── requestLogger.ts    # Request logging
├── routes/                 # Route definitions
└── db/
    └── data-source.ts      # TypeORM DataSource config
migrations/                 # TypeORM migration files
tests/
├── unit/                   # Unit tests
└── integration/            # Integration tests (supertest)
```

## Error Responses

All errors return consistent JSON:

```json
{ "error": "Error message here" }
```

- **404** — Unknown routes return `{ "error": "Not Found" }`
- **400** — Validation errors return the specific message
- **500** — Unhandled errors return `{ "error": "Internal Server Error" }`
