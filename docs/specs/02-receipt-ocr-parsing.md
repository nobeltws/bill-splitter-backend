# Feature 2: Receipt OCR & Parsing

## Scope

Accept an uploaded receipt image, extract text via docTR, and parse it into structured item data using regex heuristics with spatial awareness from bounding box positions. This endpoint is stateless — it does not persist anything.

## What This Includes

- Image upload endpoint with file size/type validation
- docTR integration (PyTorch backend, CPU inference)
  - Detection model: `db_resnet50`
  - Recognition model: `crnn_vgg16_bn`
- Spatial-aware line reconstruction from word bounding boxes
- Regex-based heuristic parser to extract:
  - Line items (name, quantity, unit price)
  - Subtotal
  - Tax/GST amount
  - Service charge amount
- Blacklist filtering (ignore lines like "TOTAL", "CASH", "VISA", etc.)
- Per-item confidence scores (from docTR word confidence)
- Structured JSON response with parsed data

## How It Works

1. **Image upload** — validate file type and size
2. **Pre-processing** — auto-orient image (EXIF), resize if > 4000px on longest side
3. **docTR inference** — returns words with bounding box coordinates and confidence scores
4. **Line reconstruction** — group words into logical lines based on vertical proximity (y-coordinate clustering)
5. **Column detection** — identify price column (right-aligned numeric values) vs item names (left-aligned text)
6. **Parsing** — apply regex heuristics to reconstructed lines to extract items, tax, service charge
7. **Response** — return structured JSON

## API

```
POST /api/receipts/parse
Content-Type: multipart/form-data
Body: { image: <file> }

Response 200:
{
  "items": [
    { "name": "Chicken Rice", "quantity": 2, "unitPrice": 6.50, "confidence": 0.92 }
  ],
  "tax": 1.20,
  "serviceCharge": 2.00,
  "rawText": "...",
  "wordBoxes": [
    { "text": "Chicken", "bbox": [0.05, 0.12, 0.25, 0.15], "confidence": 0.95 }
  ]
}
```

### Response Fields

- `items` — parsed line items with name, quantity, unit price, and confidence (0-1)
- `tax` — extracted tax/GST amount (0 if not found)
- `serviceCharge` — extracted service charge amount (0 if not found)
- `rawText` — full reconstructed text for debugging/frontend correction UI
- `wordBoxes` — word-level bounding boxes for frontend visualization (optional, can be toggled off via query param)

## Parsing Strategy

### Line Reconstruction
- Cluster words by y-coordinate (vertical center) with a tolerance threshold
- Within each cluster, sort by x-coordinate (left to right)
- Join words with spaces to form logical lines

### Column Detection
- Identify right-aligned price patterns ($X.XX) based on x-coordinate clustering
- Associate prices with the nearest item text on the same line

### Item Extraction
- Pattern: `[quantity] item_name $price` or `item_name $price`
- When multiple prices on a line: last price is the line total, first may be unit price
- Default quantity to 1 if not specified

### Tax/Service Charge
- Match patterns: `X% GST`, `TAX`, `Service Charge`, `Svc Chg`
- Extract associated dollar amount

### Blacklist
```python
BLACKLIST = [
    "total", "subtotal", "sub-total", "cash", "change",
    "visa", "mastercard", "amex", "nets", "balance",
    "thank you", "receipt", "invoice", "payment",
    "member", "points", "signature", "table",
    "pos", "rept#", "op:", "tel",
]
```

## Constraints

- Max file size: 10MB
- Accepted formats: JPEG, PNG
- docTR model loaded once at app startup (lifespan event) — not per-request
- No data is persisted; this is a pure transformation endpoint
- Inference timeout: 30 seconds (return 504 if exceeded)

## Out of Scope

- Storing the image or parsed results
- Multi-language OCR (English only for v1)
- LLM-based parsing
- Receipt template detection

## Acceptance Criteria

- Uploading a clear receipt photo returns structured items with prices and confidence scores
- Invalid file types return 400
- Oversized files return 413
- Lines containing blacklisted keywords are excluded from items
- Tax and service charge are extracted when present
- Raw OCR text is included in the response for frontend correction
- Confidence scores reflect docTR's per-word confidence
- Bounding boxes are included in response
- Response time < 10 seconds for typical receipt images on CPU
