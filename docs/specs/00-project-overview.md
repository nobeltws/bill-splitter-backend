# Bill Splitter Backend — Project Overview

## Summary

A receipt-splitting backend API built with KOA + TypeScript using the controller/service/repo pattern with PostgreSQL.

Users upload a receipt photo, the backend OCRs and parses it into structured items, then the host creates a shareable session. Participants join via link (no accounts), claim items, and see their calculated share including proportional tax/service charge. Payment is tracked via PayNow.

## Key Decisions

- **Framework:** KOA + TypeScript
- **Architecture:** Controller → Service → Repository
- **Database:** PostgreSQL
- **OCR:** Tesseract.js running on the backend
- **Auth:** None — anonymous, link-based sessions
- **Real-time:** Polling/refresh for v1 (no WebSockets)
- **Item editing:** Host edits locally on frontend, submits finalized list once
- **Payments:** Backend stores host's PayNow ID; participants generate QR client-side

## Feature Specs (Build Order)

1. [Project Foundation](./01-project-foundation.md)
2. [Receipt OCR & Parsing](./02-receipt-ocr-parsing.md)
3. [Session Management](./03-session-management.md)
4. [Item Claiming](./04-item-claiming.md)
5. [Bill Calculation](./05-bill-calculation.md)
6. [Payment Status](./06-payment-status.md)

## Data Model (High-Level)

```
Session
├── id (UUID, shareable)
├── host_paynow_id (string)
├── tax (decimal)
├── service_charge (decimal)
├── discount (decimal)
├── created_at
│
├── Items[]
│   ├── id
│   ├── name
│   ├── quantity
│   ├── unit_price
│   │
│   └── Claims[]
│       ├── participant_name
│       └── quantity_claimed
│
└── Payments[]
    ├── participant_name
    └── paid (boolean)
```
