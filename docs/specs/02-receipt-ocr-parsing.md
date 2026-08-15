# Feature 2: Receipt OCR & Parsing

## Scope

Accept an uploaded receipt image, extract text via Tesseract.js, and parse it into structured item data using regex heuristics. This endpoint is stateless — it does not persist anything.

## What This Includes

- Image upload endpoint with file size/type validation
- Tesseract.js OCR integration (English language)
- Regex-based heuristic parser to extract:
  - Line items (name, quantity, unit price)
  - Subtotal
  - Tax/GST amount
  - Service charge amount
- Blacklist filtering (ignore lines like "TOTAL", "CASH", "VISA", etc.)
- Structured JSON response with parsed data + confidence indicators

## API

```
POST /api/receipts/parse
Content-Type: multipart/form-data
Body: { image: <file> }

Response 200:
{
  "items": [
    { "name": "Chicken Rice", "quantity": 2, "unitPrice": 6.50 }
  ],
  "tax": 1.20,
  "serviceCharge": 2.00,
  "rawText": "..." // for debugging/frontend correction UI
}
```

## Constraints

- Max file size: 10MB
- Accepted formats: JPEG, PNG
- Tesseract runs synchronously — consider request timeout handling
- No data is persisted; this is a pure transformation endpoint

## Out of Scope

- Storing the image or parsed results
- Multi-language OCR
- Machine learning-based parsing
- Receipt template detection

## Acceptance Criteria

- Uploading a clear receipt photo returns structured items with prices
- Invalid file types return 400
- Oversized files return 413
- Lines containing blacklisted keywords are excluded from items
- Tax and service charge are extracted when present
- Raw OCR text is included in the response for frontend correction
