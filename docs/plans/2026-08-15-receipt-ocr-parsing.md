# Receipt OCR & Parsing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a stateless endpoint that accepts a receipt image, OCRs it via Tesseract.js, and returns structured item data (names, quantities, prices, tax, service charge).

**Architecture:** Controller handles file validation and orchestration. OCR service wraps Tesseract.js (text extraction). Receipt parser service applies regex heuristics to the raw text to extract structured data. The parser is pure logic (no I/O) — the primary unit test target.

**Tech Stack:** KOA, koa-body (multipart uploads), Tesseract.js, Jest + supertest

---

## File Structure

```
src/
├── controllers/
│   └── receipt.controller.ts    # Validates upload, calls services, returns response
├── services/
│   ├── ocr.service.ts           # Wraps Tesseract.js — image buffer → raw text
│   └── receipt-parser.service.ts # Raw text → structured items (pure logic)
├── routes/
│   └── index.ts                 # (modify) Add POST /api/receipts/parse
├── app.ts                       # (modify) Add koa-body middleware for multipart
tests/
├── unit/
│   └── services/
│       └── receipt-parser.test.ts # Parser logic tests (many cases)
├── integration/
│   └── receipt-parse.test.ts    # Endpoint tests (validation, happy path)
├── fixtures/
│   └── sample-receipt.txt       # Sample OCR text for parser tests
```

---

### Task 1: Receipt parser service (TDD — pure logic)

**Files:**
- Create: `src/services/receipt-parser.service.ts`
- Create: `tests/unit/services/receipt-parser.test.ts`
- Create: `tests/fixtures/sample-receipt.txt`

- [ ] **Step 1: Create sample receipt fixture**

Create `tests/fixtures/sample-receipt.txt`:
```
RESTAURANT ABC
123 Main Street
Tel: 6512 3456

Table 5
2024-01-15 19:30

2x Chicken Rice         13.00
1x Laksa                8.50
Fish & Chips            15.00
3x Iced Tea             9.00

Subtotal               45.50
Service Charge         4.55
GST                    3.64
Total                  53.69

VISA ****1234
Thank you!
```

- [ ] **Step 2: Write the failing tests**

```typescript
// tests/unit/services/receipt-parser.test.ts
import { parseReceiptText, ParsedReceipt } from "../../../src/services/receipt-parser.service";
import * as fs from "fs";
import * as path from "path";

const sampleReceipt = fs.readFileSync(
  path.join(__dirname, "../../fixtures/sample-receipt.txt"),
  "utf-8"
);

describe("receipt-parser.service", () => {
  describe("parseReceiptText", () => {
    let result: ParsedReceipt;

    beforeAll(() => {
      result = parseReceiptText(sampleReceipt);
    });

    it("extracts line items with quantity and price", () => {
      expect(result.items).toEqual(
        expect.arrayContaining([
          { name: "Chicken Rice", quantity: 2, unitPrice: 6.50 },
          { name: "Laksa", quantity: 1, unitPrice: 8.50 },
          { name: "Fish & Chips", quantity: 1, unitPrice: 15.00 },
          { name: "Iced Tea", quantity: 3, unitPrice: 3.00 },
        ])
      );
    });

    it("extracts tax/GST amount", () => {
      expect(result.tax).toBe(3.64);
    });

    it("extracts service charge", () => {
      expect(result.serviceCharge).toBe(4.55);
    });

    it("filters out blacklisted lines (total, visa, etc.)", () => {
      const itemNames = result.items.map((i) => i.name.toLowerCase());
      expect(itemNames).not.toContain("total");
      expect(itemNames).not.toContain("subtotal");
      expect(itemNames).not.toContain("visa");
    });

    it("returns 0 for tax when not present", () => {
      const noTaxReceipt = "1x Coffee  5.00\nSubtotal  5.00\nTotal  5.00";
      const parsed = parseReceiptText(noTaxReceipt);
      expect(parsed.tax).toBe(0);
    });

    it("returns 0 for service charge when not present", () => {
      const noScReceipt = "1x Coffee  5.00\nSubtotal  5.00\nTotal  5.00";
      const parsed = parseReceiptText(noScReceipt);
      expect(parsed.serviceCharge).toBe(0);
    });

    it("handles items without explicit quantity prefix", () => {
      const text = "Fish & Chips  15.00";
      const parsed = parseReceiptText(text);
      expect(parsed.items[0]).toEqual({
        name: "Fish & Chips",
        quantity: 1,
        unitPrice: 15.00,
      });
    });
  });
});
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `npx jest tests/unit/services/receipt-parser.test.ts`
Expected: FAIL — cannot find module `../../../src/services/receipt-parser.service`

- [ ] **Step 4: Implement the receipt parser**

```typescript
// src/services/receipt-parser.service.ts
export interface ParsedItem {
  name: string;
  quantity: number;
  unitPrice: number;
}

export interface ParsedReceipt {
  items: ParsedItem[];
  tax: number;
  serviceCharge: number;
}

const BLACKLIST = [
  "total", "subtotal", "sub-total", "cash", "change",
  "visa", "mastercard", "amex", "nets", "balance",
  "thank you", "receipt", "invoice",
];

const ITEM_REGEX = /^(?:(\d+)\s*[xX]\s+)?(.+?)\s{2,}(\d+\.\d{2})$/;
const TAX_REGEX = /(gst|tax|vat)\s*[:]?\s*(\d+\.\d{2})/i;
const SERVICE_CHARGE_REGEX = /(service\s*charge|serv\.?\s*chg|svc)\s*[:]?\s*(\d+\.\d{2})/i;

function isBlacklisted(line: string): boolean {
  const lower = line.toLowerCase();
  return BLACKLIST.some((word) => lower.includes(word));
}

export function parseReceiptText(rawText: string): ParsedReceipt {
  const lines = rawText.split("\n").map((l) => l.trim()).filter((l) => l.length > 0);

  let tax = 0;
  let serviceCharge = 0;
  const items: ParsedItem[] = [];

  for (const line of lines) {
    const taxMatch = line.match(TAX_REGEX);
    if (taxMatch) {
      tax = parseFloat(taxMatch[2]);
      continue;
    }

    const scMatch = line.match(SERVICE_CHARGE_REGEX);
    if (scMatch) {
      serviceCharge = parseFloat(scMatch[2]);
      continue;
    }

    if (isBlacklisted(line)) {
      continue;
    }

    const itemMatch = line.match(ITEM_REGEX);
    if (itemMatch) {
      const quantity = itemMatch[1] ? parseInt(itemMatch[1], 10) : 1;
      const totalPrice = parseFloat(itemMatch[3]);
      items.push({
        name: itemMatch[2].trim(),
        quantity,
        unitPrice: Math.round((totalPrice / quantity) * 100) / 100,
      });
    }
  }

  return { items, tax, serviceCharge };
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `npx jest tests/unit/services/receipt-parser.test.ts`
Expected: PASS (7 tests)

- [ ] **Step 6: Commit**

```bash
git add src/services/receipt-parser.service.ts tests/unit/services/receipt-parser.test.ts tests/fixtures/sample-receipt.txt
git commit -m "feat: add receipt parser service with regex heuristics"
```

---

### Task 2: OCR service (Tesseract.js wrapper)

**Files:**
- Create: `src/services/ocr.service.ts`

- [ ] **Step 1: Install Tesseract.js**

Run:
```bash
npm install tesseract.js
```

- [ ] **Step 2: Write the OCR service**

```typescript
// src/services/ocr.service.ts
import { createWorker } from "tesseract.js";

export async function extractTextFromImage(imageBuffer: Buffer): Promise<string> {
  const worker = await createWorker("eng");
  try {
    const { data } = await worker.recognize(imageBuffer);
    return data.text;
  } finally {
    await worker.terminate();
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add src/services/ocr.service.ts package.json package-lock.json
git commit -m "feat: add OCR service wrapping Tesseract.js"
```

---

### Task 3: Receipt controller with file validation

**Files:**
- Create: `src/controllers/receipt.controller.ts`
- Modify: `src/routes/index.ts`
- Modify: `src/app.ts`

- [ ] **Step 1: Write the receipt controller**

```typescript
// src/controllers/receipt.controller.ts
import { Context } from "koa";
import { extractTextFromImage } from "../services/ocr.service";
import { parseReceiptText } from "../services/receipt-parser.service";

const ALLOWED_TYPES = ["image/jpeg", "image/png"];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export async function parseReceipt(ctx: Context): Promise<void> {
  const file = ctx.request.files?.image;

  if (!file || Array.isArray(file)) {
    ctx.status = 400;
    ctx.body = { error: "A single image file is required in the 'image' field" };
    return;
  }

  if (!ALLOWED_TYPES.includes(file.mimetype || "")) {
    ctx.status = 400;
    ctx.body = { error: "Only JPEG and PNG files are accepted" };
    return;
  }

  if (file.size > MAX_FILE_SIZE) {
    ctx.status = 413;
    ctx.body = { error: "File size exceeds 10MB limit" };
    return;
  }

  const fs = await import("fs/promises");
  const imageBuffer = await fs.readFile(file.filepath);

  const rawText = await extractTextFromImage(imageBuffer);
  const parsed = parseReceiptText(rawText);

  ctx.status = 200;
  ctx.body = {
    items: parsed.items,
    tax: parsed.tax,
    serviceCharge: parsed.serviceCharge,
    rawText,
  };
}
```

- [ ] **Step 2: Add the route**

Update `src/routes/index.ts`:
```typescript
import Router from "@koa/router";
import { healthCheck } from "../controllers/health.controller";
import { parseReceipt } from "../controllers/receipt.controller";

const router = new Router();

router.get("/health", healthCheck);
router.post("/api/receipts/parse", parseReceipt);

export default router;
```

- [ ] **Step 3: Add koa-body middleware for multipart uploads**

Update `src/app.ts`:
```typescript
import Koa from "koa";
import cors from "@koa/cors";
import { koaBody } from "koa-body";
import { errorHandler } from "./middleware/errorHandler";
import { notFound } from "./middleware/notFound";
import { requestLogger } from "./middleware/requestLogger";
import router from "./routes";

const app = new Koa();

app.use(errorHandler);
app.use(requestLogger);
app.use(cors());
app.use(koaBody({
  multipart: true,
  formidable: {
    maxFileSize: 10 * 1024 * 1024,
  },
}));
app.use(router.routes());
app.use(router.allowedMethods());
app.use(notFound);

export default app;
```

- [ ] **Step 4: Commit**

```bash
git add src/controllers/receipt.controller.ts src/routes/index.ts src/app.ts
git commit -m "feat: add receipt parse endpoint with file validation"
```

---

### Task 4: Integration tests for the endpoint

**Files:**
- Create: `tests/integration/receipt-parse.test.ts`
- Create: `tests/fixtures/test-image.png`

- [ ] **Step 1: Create a minimal test image fixture**

We need a tiny valid PNG for testing file type validation. Create a 1x1 pixel PNG programmatically in the test, and also test with a `.txt` file for rejection.

- [ ] **Step 2: Write integration tests**

```typescript
// tests/integration/receipt-parse.test.ts
import request from "supertest";
import path from "path";
import fs from "fs";
import app from "../../src/app";

// Create a minimal valid PNG (1x1 pixel) for testing
const MINIMAL_PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "base64"
);

describe("POST /api/receipts/parse", () => {
  it("returns 400 when no file is provided", async () => {
    const res = await request(app.callback())
      .post("/api/receipts/parse")
      .send({});

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/image/i);
  });

  it("returns 400 for invalid file types", async () => {
    const res = await request(app.callback())
      .post("/api/receipts/parse")
      .attach("image", Buffer.from("not an image"), {
        filename: "test.txt",
        contentType: "text/plain",
      });

    expect(res.status).toBe(400);
    expect(res.body.error).toMatch(/JPEG|PNG/i);
  });

  it("returns 200 with parsed data for a valid image", async () => {
    const res = await request(app.callback())
      .post("/api/receipts/parse")
      .attach("image", MINIMAL_PNG, {
        filename: "receipt.png",
        contentType: "image/png",
      });

    // Minimal 1x1 PNG won't have meaningful OCR text, but the endpoint should succeed
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty("items");
    expect(res.body).toHaveProperty("tax");
    expect(res.body).toHaveProperty("serviceCharge");
    expect(res.body).toHaveProperty("rawText");
    expect(Array.isArray(res.body.items)).toBe(true);
  });
});
```

- [ ] **Step 3: Run integration tests**

Run: `npx jest tests/integration/receipt-parse.test.ts`
Expected: PASS (3 tests)

- [ ] **Step 4: Run all tests**

Run: `npx jest`
Expected: PASS (all tests — unit parser tests + unit middleware tests + integration tests)

- [ ] **Step 5: Commit**

```bash
git add tests/integration/receipt-parse.test.ts
git commit -m "test: add integration tests for receipt parse endpoint"
```

---

### Task 5: Verify full test suite and build

**Files:** (none — verification only)

- [ ] **Step 1: Run full test suite**

Run: `npx jest`
Expected: All tests pass

- [ ] **Step 2: Verify build compiles**

Run: `npm run build`
Expected: No errors

- [ ] **Step 3: Commit if any changes needed**

```bash
git add -A
git commit -m "chore: verify build and tests pass" --allow-empty
```

---

## Spec Coverage Check

| Requirement | Task |
|---|---|
| Image upload endpoint | Task 3 |
| File size validation (10MB) | Task 3 |
| File type validation (JPEG, PNG) | Task 3, 4 |
| Invalid file types return 400 | Task 3, 4 |
| Oversized files return 413 | Task 3 |
| Tesseract.js OCR integration | Task 2 |
| Regex-based heuristic parser | Task 1 |
| Extract line items (name, quantity, unit price) | Task 1 |
| Extract tax/GST | Task 1 |
| Extract service charge | Task 1 |
| Blacklist filtering | Task 1 |
| Raw OCR text in response | Task 3 |
| Stateless (no persistence) | Task 3 (no DB calls) |
| Structured JSON response | Task 3 |
