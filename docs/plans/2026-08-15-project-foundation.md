# Project Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold a KOA + TypeScript backend with controller/service/repo architecture, PostgreSQL connection, and baseline middleware.

**Architecture:** KOA HTTP server with layered architecture (controller → service → repo). PostgreSQL via TypeORM (ORM + migrations). Middleware stack: request logger → CORS → error handler → router.

**Tech Stack:** KOA, TypeScript, PostgreSQL, TypeORM (ORM + migrations), dotenv, tsx (dev), Jest (testing)

---

## File Structure

```
src/
├── app.ts                  # KOA app setup (middleware, router mounting)
├── server.ts               # Entry point (starts server, initializes TypeORM)
├── config/
│   └── index.ts            # Environment config (reads .env, exports typed config)
├── db/
│   └── data-source.ts      # TypeORM DataSource configuration
├── entities/               # TypeORM entity classes (empty for now)
├── middleware/
│   ├── errorHandler.ts     # Catches errors, returns consistent JSON
│   ├── notFound.ts         # 404 for unmatched routes
│   └── requestLogger.ts    # Logs method, path, status, duration
├── controllers/
│   └── health.controller.ts # GET /health handler
├── routes/
│   └── index.ts            # Mounts all route groups
├── services/               # (empty for now, structure only)
├── repos/                  # (empty for now, structure only)
migrations/                 # TypeORM migration files (empty for now)
tests/
├── integration/
│   └── health.test.ts      # Supertest integration test for GET /health
├── unit/
│   └── middleware/
│       └── errorHandler.test.ts
.env.example                # Template for required env vars
```

---

### Task 1: Initialize project and install dependencies

**Files:**
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `.env.example`
- Create: `.gitignore`

- [ ] **Step 1: Initialize npm project**

Run:
```bash
npm init -y
```

- [ ] **Step 2: Install production dependencies**

Run:
```bash
npm install koa @koa/router @koa/cors koa-body typeorm reflect-metadata pg dotenv
```

- [ ] **Step 3: Install dev dependencies**

Run:
```bash
npm install -D typescript @types/node @types/koa @types/koa__router @types/koa__cors @types/pg tsx jest ts-jest @types/jest supertest @types/supertest
```

- [ ] **Step 4: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "emitDecoratorMetadata": true,
    "experimentalDecorators": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

- [ ] **Step 5: Create .env.example**

```
PORT=3000
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/bill_splitter
NODE_ENV=development
```

- [ ] **Step 6: Create .gitignore**

```
node_modules/
dist/
.env
*.log
```

- [ ] **Step 7: Add scripts to package.json**

Update the `"scripts"` section:
```json
{
  "scripts": {
    "dev": "tsx watch src/server.ts",
    "build": "tsc",
    "start": "node dist/server.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "typeorm": "tsx node_modules/typeorm/cli.js",
    "migration:generate": "npm run typeorm -- migration:generate -d src/db/data-source.ts",
    "migration:run": "npm run typeorm -- migration:run -d src/db/data-source.ts",
    "migration:revert": "npm run typeorm -- migration:revert -d src/db/data-source.ts"
  }
}
```

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "chore: initialize project with dependencies and config"
```

---

### Task 2: Config module

**Files:**
- Create: `src/config/index.ts`

- [ ] **Step 1: Write the config module**

```typescript
// src/config/index.ts
import dotenv from "dotenv";

dotenv.config();

export const config = {
  port: parseInt(process.env.PORT || "3000", 10),
  databaseUrl: process.env.DATABASE_URL || "postgresql://postgres:postgres@localhost:5432/bill_splitter",
  nodeEnv: process.env.NODE_ENV || "development",
};
```

- [ ] **Step 2: Commit**

```bash
git add src/config/index.ts
git commit -m "feat: add config module"
```

---

### Task 3: Database connection (TypeORM)

**Files:**
- Create: `src/db/data-source.ts`

- [ ] **Step 1: Write the TypeORM DataSource configuration**

```typescript
// src/db/data-source.ts
import "reflect-metadata";
import { DataSource } from "typeorm";
import { config } from "../config";

export const AppDataSource = new DataSource({
  type: "postgres",
  url: config.databaseUrl,
  synchronize: false,
  logging: config.nodeEnv === "development",
  entities: [__dirname + "/../entities/**/*.{ts,js}"],
  migrations: [__dirname + "/../../migrations/**/*.{ts,js}"],
});
```

- [ ] **Step 2: Create the entities and migrations directories**

Run:
```bash
mkdir -p src/entities migrations
```

- [ ] **Step 3: Commit**

```bash
git add src/db/data-source.ts src/entities/ migrations/
git commit -m "feat: add TypeORM DataSource configuration"
```

---

### Task 4: Error handling middleware (TDD)

**Files:**
- Create: `src/middleware/errorHandler.ts`
- Create: `tests/unit/middleware/errorHandler.test.ts`

- [ ] **Step 1: Create Jest config**

Create `jest.config.ts`:
```typescript
import type { Config } from "jest";

const config: Config = {
  preset: "ts-jest",
  testEnvironment: "node",
  roots: ["<rootDir>/tests"],
  testMatch: ["**/*.test.ts"],
};

export default config;
```

- [ ] **Step 2: Write the failing test**

```typescript
// tests/unit/middleware/errorHandler.test.ts
import Koa from "koa";
import request from "supertest";
import { errorHandler } from "../../../src/middleware/errorHandler";

function createTestApp(middleware: Koa.Middleware, routeHandler: Koa.Middleware): Koa {
  const app = new Koa();
  app.use(middleware);
  app.use(routeHandler);
  return app;
}

describe("errorHandler middleware", () => {
  it("returns 500 with JSON body for unhandled errors", async () => {
    const app = createTestApp(errorHandler, async () => {
      throw new Error("something broke");
    });

    const res = await request(app.callback()).get("/");

    expect(res.status).toBe(500);
    expect(res.body).toEqual({ error: "Internal Server Error" });
  });

  it("returns custom status code when error has status property", async () => {
    const app = createTestApp(errorHandler, async () => {
      const err: any = new Error("bad input");
      err.status = 400;
      throw err;
    });

    const res = await request(app.callback()).get("/");

    expect(res.status).toBe(400);
    expect(res.body).toEqual({ error: "bad input" });
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `npx jest tests/unit/middleware/errorHandler.test.ts`
Expected: FAIL — cannot find module `../../../src/middleware/errorHandler`

- [ ] **Step 4: Write minimal implementation**

```typescript
// src/middleware/errorHandler.ts
import { Context, Next } from "koa";

export async function errorHandler(ctx: Context, next: Next): Promise<void> {
  try {
    await next();
  } catch (err: any) {
    const status = err.status || 500;
    const message = status === 500 ? "Internal Server Error" : err.message;
    ctx.status = status;
    ctx.body = { error: message };
  }
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npx jest tests/unit/middleware/errorHandler.test.ts`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add jest.config.ts tests/unit/middleware/errorHandler.test.ts src/middleware/errorHandler.ts
git commit -m "feat: add error handling middleware with tests"
```

---

### Task 5: Not-found and request logger middleware

**Files:**
- Create: `src/middleware/notFound.ts`
- Create: `src/middleware/requestLogger.ts`

- [ ] **Step 1: Write the notFound middleware**

```typescript
// src/middleware/notFound.ts
import { Context, Next } from "koa";

export async function notFound(ctx: Context, next: Next): Promise<void> {
  await next();
  if (ctx.status === 404 && !ctx.body) {
    ctx.status = 404;
    ctx.body = { error: "Not Found" };
  }
}
```

- [ ] **Step 2: Write the requestLogger middleware**

```typescript
// src/middleware/requestLogger.ts
import { Context, Next } from "koa";

export async function requestLogger(ctx: Context, next: Next): Promise<void> {
  const start = Date.now();
  await next();
  const duration = Date.now() - start;
  console.log(`${ctx.method} ${ctx.path} ${ctx.status} ${duration}ms`);
}
```

- [ ] **Step 3: Commit**

```bash
git add src/middleware/notFound.ts src/middleware/requestLogger.ts
git commit -m "feat: add notFound and requestLogger middleware"
```

---

### Task 6: Health controller and router

**Files:**
- Create: `src/controllers/health.controller.ts`
- Create: `src/routes/index.ts`

- [ ] **Step 1: Write the health controller**

```typescript
// src/controllers/health.controller.ts
import { Context } from "koa";

export async function healthCheck(ctx: Context): Promise<void> {
  ctx.status = 200;
  ctx.body = { status: "ok" };
}
```

- [ ] **Step 2: Write the router**

```typescript
// src/routes/index.ts
import Router from "@koa/router";
import { healthCheck } from "../controllers/health.controller";

const router = new Router();

router.get("/health", healthCheck);

export default router;
```

- [ ] **Step 3: Commit**

```bash
git add src/controllers/health.controller.ts src/routes/index.ts
git commit -m "feat: add health check controller and router"
```

---

### Task 7: App and server entry point

**Files:**
- Create: `src/app.ts`
- Create: `src/server.ts`
- Create: `src/services/.gitkeep`
- Create: `src/repos/.gitkeep`

- [ ] **Step 1: Write the KOA app (middleware composition)**

```typescript
// src/app.ts
import Koa from "koa";
import cors from "@koa/cors";
import { errorHandler } from "./middleware/errorHandler";
import { notFound } from "./middleware/notFound";
import { requestLogger } from "./middleware/requestLogger";
import router from "./routes";

const app = new Koa();

app.use(errorHandler);
app.use(requestLogger);
app.use(cors());
app.use(router.routes());
app.use(router.allowedMethods());
app.use(notFound);

export default app;
```

- [ ] **Step 2: Write the server entry point**

```typescript
// src/server.ts
import "reflect-metadata";
import app from "./app";
import { config } from "./config";
import { AppDataSource } from "./db/data-source";

async function start(): Promise<void> {
  try {
    await AppDataSource.initialize();
    console.log("Database connected");
  } catch (err) {
    console.error("Failed to connect to database:", err);
    process.exit(1);
  }

  app.listen(config.port, () => {
    console.log(`Server running on port ${config.port}`);
  });
}

start();
```

- [ ] **Step 3: Create placeholder directories**

Run:
```bash
mkdir -p src/services src/repos
touch src/services/.gitkeep src/repos/.gitkeep
```

- [ ] **Step 4: Commit**

```bash
git add src/app.ts src/server.ts src/services/.gitkeep src/repos/.gitkeep
git commit -m "feat: add KOA app and server entry point with TypeORM initialization"
```

---

### Task 8: Integration test for health endpoint

**Files:**
- Create: `tests/integration/health.test.ts`

- [ ] **Step 1: Write the integration test**

```typescript
// tests/integration/health.test.ts
import request from "supertest";
import app from "../../src/app";

describe("GET /health", () => {
  it("returns 200 with status ok", async () => {
    const res = await request(app.callback()).get("/health");

    expect(res.status).toBe(200);
    expect(res.body).toEqual({ status: "ok" });
  });
});

describe("Unknown routes", () => {
  it("returns 404 with JSON error for unknown paths", async () => {
    const res = await request(app.callback()).get("/unknown");

    expect(res.status).toBe(404);
    expect(res.body).toEqual({ error: "Not Found" });
  });
});
```

- [ ] **Step 2: Run the integration test**

Run: `npx jest tests/integration/health.test.ts`
Expected: PASS (2 tests)

- [ ] **Step 3: Run all tests**

Run: `npx jest`
Expected: PASS (4 tests total — 2 unit + 2 integration)

- [ ] **Step 4: Commit**

```bash
git add tests/integration/health.test.ts
git commit -m "test: add integration tests for health and 404 routes"
```

---

### Task 9: Verify dev and build scripts work

**Files:** (none — verification only)

- [ ] **Step 1: Verify the build compiles**

Run: `npm run build`
Expected: No errors, `dist/` directory created with `.js` files

- [ ] **Step 2: Verify dev mode starts (manual check)**

Run: `npm run dev`
Expected: Console shows "Server running on port 3000" (will fail DB connection if no local Postgres — that's expected at this stage)

Stop with Ctrl+C.

- [ ] **Step 3: Add dist to .gitignore if not already present, final commit**

Run: `npx jest`
Expected: All tests pass.

```bash
git add -A
git commit -m "chore: verify build and dev scripts work" --allow-empty
```

---

## Spec Coverage Check

| Requirement | Task |
|---|---|
| TypeScript + KOA project setup | Task 1 |
| Folder structure (controllers/services/repos/middleware/config) | Tasks 2-7 |
| PostgreSQL connection (TypeORM DataSource) | Task 3 |
| Database migration tooling (TypeORM migrations) | Task 3 |
| Error handling middleware | Task 4 |
| Request logging middleware | Task 5 |
| CORS configuration | Task 7 |
| Health check endpoint | Tasks 6, 8 |
| Environment config management | Task 2 |
| `npm run dev` with hot reload | Tasks 1, 9 |
| `npm run build` produces production build | Tasks 1, 9 |
| Invalid routes return 404 JSON | Tasks 5, 8 |
| Unhandled errors return 500 JSON | Task 4 |
