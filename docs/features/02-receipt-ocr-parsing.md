# Feature 2: Receipt OCR & Parsing

## Summary

A stateless endpoint that accepts a receipt image, extracts text via Tesseract.js OCR, and returns structured item data using regex-based heuristics.

## What Was Built

### Endpoint

```
POST /api/receipts/parse
Content-Type: multipart/form-data
Body: { image: <file> }
```

**Response 200:**
```json
{
  "items": [
    { "name": "Chicken Rice", "quantity": 2, "unitPrice": 6.50 }
  ],
  "tax": 3.64,
  "serviceCharge": 4.55,
  "rawText": "..."
}
```

### Validation

| Condition | Response |
|-----------|----------|
| No file provided | 400 — `A single image file is required in the 'image' field` |
| Invalid file type | 400 — `Only JPEG and PNG files are accepted` |
| File > 10MB | 413 — `File size exceeds 10MB limit` |

### Components

| File | Responsibility |
|------|---------------|
| `src/controllers/receipt.controller.ts` | Validates upload, orchestrates OCR + parsing, returns response |
| `src/services/ocr.service.ts` | Wraps Tesseract.js — image buffer → raw text |
| `src/services/receipt-parser.service.ts` | Pure logic — raw text → structured items via regex |

### Parser Heuristics

The receipt parser uses regex patterns to extract data:

- **Item regex:** Matches lines like `2x Chicken Rice  13.00` or `Fish & Chips  15.00`
  - Captures optional quantity prefix (`Nx`), item name, and trailing price
  - Calculates `unitPrice` as `totalPrice / quantity`
- **Tax regex:** Matches lines containing GST/tax/VAT followed by a decimal amount
- **Service charge regex:** Matches lines containing "service charge" or abbreviations
- **Blacklist:** Lines containing total, subtotal, cash, change, visa, mastercard, etc. are skipped

### Middleware Addition

`koa-body` middleware was added to `src/app.ts` with multipart support for file uploads (10MB max).

## Testing

- 14 tests total across 4 suites
- Run with `npm test`

### Unit Tests (7 tests)
- `tests/unit/services/receipt-parser.test.ts`
  - Extracts items with quantity and price
  - Extracts tax/GST
  - Extracts service charge
  - Filters blacklisted lines
  - Defaults to 0 when tax/service charge absent
  - Handles items without quantity prefix

### Integration Tests (3 tests)
- `tests/integration/receipt-parse.test.ts`
  - Returns 400 when no file provided
  - Returns 400 for invalid file types
  - Returns 200 with correct response shape for valid PNG

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Stateless endpoint | No persistence — frontend edits results before creating a session |
| `rawText` in response | Allows frontend to show OCR output for manual correction |
| Unit price calculated from total | Receipts show line total (qty × price), we derive unit price |
| Tesseract worker created per-request | Avoids memory leaks from long-lived workers; acceptable for low-volume use |
| koa-body over multer | Already installed, native KOA support, simpler API |

## Limitations

- OCR accuracy depends on image quality and receipt formatting
- Regex parser assumes a specific receipt layout (price at end of line, separated by 2+ spaces)
- Single-language support (English only)
- No receipt template detection — one-size-fits-all heuristics
