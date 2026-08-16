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
  - Tax/GST amount
  - Service charge amount
- Blacklist filtering (ignore lines like "TOTAL", "CASH", "VISA", etc.)
- Confidence threshold filtering (items below 0.9 average confidence are excluded)
- Per-item confidence scores (from docTR word confidence)
- Structured JSON response with parsed data

## How It Works

1. **Image upload** — validate file type (JPEG/PNG) and size (max 10MB)
2. **Pre-processing** — auto-orient image (EXIF), resize if > 4000px on longest side, convert to RGB
3. **docTR inference** — returns words with bounding box coordinates and confidence scores
4. **Oversized word filtering** — remove OCR artifacts with bounding boxes > 2.5x the median height
5. **Line reconstruction** — group words into logical lines based on vertical proximity (y-coordinate clustering with anchor-based comparison to prevent line drift)
6. **Parsing** — apply regex heuristics to reconstructed lines to extract items, tax, service charge
7. **Confidence filtering** — exclude items with average line confidence < 0.9
8. **Response** — return structured JSON

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
  "rawText": "..."
}
```

### Response Fields

- `items` — parsed line items with name, quantity, unit price, and confidence (0-1). Only items with confidence >= 0.9 are included.
- `tax` — extracted tax/GST amount (0 if not found)
- `serviceCharge` — extracted service charge amount (0 if not found)
- `rawText` — full reconstructed text for debugging/frontend correction UI

### Error Responses

- `400` — invalid file type (not JPEG/PNG)
- `413` — file size exceeds 10MB
- `503` — OCR model not available

## Parsing Strategy

### Line Reconstruction
- Filter out oversized bounding boxes (> 2.5x median word height) that are OCR artifacts
- Cluster words by y-coordinate using anchor-based comparison (tolerance: 0.01 in normalized coordinates)
  - Each new word is compared to the first word's y-center in the current line (not the previous word), preventing gradual drift between adjacent lines
- Within each cluster, sort by x-coordinate (left to right)
- Join words with spaces to form logical lines

### Item Extraction
- Pattern: `[quantity] item_name $price` or `item_name $price`
- Price regex matches `$X.XX` and `$X.X` formats (1-2 decimal places)
- When multiple prices on a line: last price is used as the line total
- Default quantity to 1 if not specified
- Unit price = total price / quantity

### Tax/Service Charge
- Tax: match patterns like `X% GST`, `X% TAX`, `X% VAT`
- Service charge: match patterns like `Service Charge`, `Svr Chrg`, `Svc`
- Extract the last dollar amount on the matched line

### Blacklist
```python
BLACKLIST = [
    "total", "subtotal", "sub-total", "cash", "change",
    "visa", "mastercard", "amex", "nets", "balance",
    "thank you", "receipt", "invoice", "payment",
    "member", "points", "signature", "table",
    "pos", "rept#", "op:", "tel", "sts",
]
```

## Constraints

- Max file size: 10MB
- Accepted formats: JPEG, PNG
- docTR model loaded once at app startup (lifespan event) — not per-request
- No data is persisted; this is a pure transformation endpoint
- Confidence threshold: 0.9 (items below this are excluded for manual review later)

## Out of Scope

- Storing the image or parsed results
- Multi-language OCR (English only for v1)
- LLM-based parsing
- Receipt template detection
- Manual item review/correction UI (planned for later feature)

## Acceptance Criteria

- Uploading a clear receipt photo returns structured items with prices and confidence scores
- Invalid file types return 400
- Oversized files return 413
- OCR model unavailable returns 503
- Lines containing blacklisted keywords are excluded from items
- Items with average confidence < 0.9 are excluded from the response
- Tax and service charge are extracted when present
- Raw OCR text is included in the response for frontend correction
- Confidence scores reflect docTR's per-word confidence averaged across the line
- Response time < 10 seconds for typical receipt images on CPU
