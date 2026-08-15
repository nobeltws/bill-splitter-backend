To build your receipt-splitting web application using React and Node.js without any AI models, you can rely on Deterministic OCR (Optical Character Recognition) via open-source libraries or cloud APIs configured for raw text extraction, followed by Regex (Regular Expressions) and coordinate-based heuristics to parse items.Since you are using React and Node.js (and already working with tech stacks like LifeSG / react-design-system or nobeltws / payment-tracker), here is a complete architectural proposal and implementation guide.1. System ArchitecturePlaintext+-------------------------------------------------------------+
| REACT FRONTEND |
| - Bill Upload Component |
| - Interactive Item-Selection & Split View |
| - SGQR / PayNow QR Code Generator & Status Tracker |
+------------------------------+------------------------------+
| (REST API / WebSockets)
+------------------------------v------------------------------+
| NODE.JS / EXPRESS BACKEND |
| - Multer (Image Upload Middleware) |
| - Tesseract.js / OCR Engine (Extract Raw Text) |
| - Heuristic Parser (Regex & Line-by-Line Tokenizer) |
| - Session / Room Manager (In-Memory / PostgreSQL / MongoDB)|
+-------------------------------------------------------------+ 2. Component BreakdownA. Frontend (React)View 1 (Host/Uploader): Uploads the receipt image, triggers processing, reviews/corrects the auto-detected items, quantities, and totals, and generates a shareable link.View 2 (Participant): Loaded via [app.com/split/:sessionId](https://app.com/split/:sessionId). Displays the itemized list. Users tap items they consumed, enter quantities, and see a real-time recalculation of their share (proportional tax, service charge, and discounts).View 3 (Settlement): Displays the host's PayNow QR Code (compliant with Singapore’s SGQR standard) and a toggle allowing users to mark “I have paid”. The host dashboard displays live statuses of who has paid.B. Backend (Node.js & Express)API Endpoints:POST /api/receipts/parse — Accepts image, performs OCR, parses text, and returns structured JSON items.POST /api/sessions — Saves the finalized bill state and returns a unique sessionId.GET /api/sessions/:id — Fetches bill state for participants.PATCH /api/sessions/:id/claims — Updates who claimed which item.PATCH /api/sessions/:id/pay-status — Marks a user's payment status.3. How to Extract Receipt Data Without AIParsing receipts without machine learning or AI models requires a pipeline combining OCR text extraction and Rule-Based Parsing (Regex & Layout Heuristics).Step 1: Text Extraction via OCRUse Tesseract.js (runs locally in Node.js) or a classic OCR utility to convert the receipt image into a raw text block with bounding boxes/line coordinates.Bashnpm install tesseract.js multer
Step 2: Line-by-Line Regex Parsing (The Heuristic Engine)Receipts follow predictable structural patterns: quantities are usually followed by an item name and a trailing price aligned to the right.Create a Node.js utility (parser.js) that uses regular expressions to isolate line items, quantities, and prices:JavaScriptconst { createWorker } = require('tesseract.js');

async function parseReceipt(imagePath) {
const worker = await createWorker('eng');
const ret = await worker.recognize(imagePath);
await worker.terminate();

const lines = ret.data.text.split('\n').filter(line => line.trim() !== '');

let items = [];
let subtotal = 0;
let taxOrGst = 0;
let serviceCharge = 0;

// Regex to match patterns like: "2x Chicken Rice 12.50" or "Chicken Rice 1. 12.50"
// Captures: Optional Quantity, Item Description, Price
const itemRegex = /^(?:(\d+)\s*[xX]?\s+)?(.+?)\s+(\d+\.\d{2})$/;
const taxRegex = /(gst|tax|vat)\s*[:]?\s*(\d+\.\d{2})/i;
const scRegex = /(service\s*charge|serv)\s*[:]?\s*(\d+\.\d{2})/i;

for (let line of lines) {
const itemMatch = line.match(itemRegex);
if (itemMatch && !isIgnoredKeyword(line)) {
items.push({
quantity: itemMatch[1] ? parseInt(itemMatch[1], 10) : 1,
name: itemMatch[2].trim(),
price: parseFloat(itemMatch[3])
});
continue;
}

    const taxMatch = line.match(taxRegex);
    if (taxMatch) {
      taxOrGst = parseFloat(taxMatch[2]);
    }

    const scMatch = line.match(scRegex);
    if (scMatch) {
      serviceCharge = parseFloat(scMatch[2]);
    }

}

return { items, taxOrGst, serviceCharge };
}

function isIgnoredKeyword(text) {
const blacklist = ['total', 'subtotal', 'cash', 'change', 'visa', 'mastercard', 'balance'];
return blacklist.some(word => text.toLowerCase().includes(word));
}

module.exports = { parseReceipt }; 4. Handling Calculations & AdjustmentsOnce items are parsed, the backend or frontend calculates individual totals dynamically when users select items:Item Share: If an item costs $10 and is shared by 2 people, each owes $5. If quantities are specified (e.g., quantity of 2), it scales accordingly.Proportional Add-ons (GST, Service Charge, Discounts):$$\text{User Final Share} = \text{Subtotal of Claimed Items} \times \left(1 + \frac{\text{Tax} + \text{Service Charge} - \text{Discount}}{\text{Raw Subtotal}}\right)$$This ensures taxes and service charges are distributed fairly based on what each person actually ordered.5. Generating a PayNow QR Code (Singapore Context)Since you are targeting local payments (indicated by standard receipt structures like GST and service charge), you can dynamically generate a SGQR / PayNow QR code on the frontend without any backend dependency using open-source npm packages like paynow-qr or qrcode.react.Bashnpm install paynow-qr qrcode.react
JavaScriptimport { QRCodeCanvas } from 'qrcode.react';
import GeneratePayNowQR from 'paynow-qr';

// Example component snippet for settlement view
function PaymentView({ payNowIdentifier, amountToPay, userPhone }) {
// Generates SGQR payload string for UEN or Mobile Number
const qrPayload = new GeneratePayNowQR({
uen: payNowIdentifier, // e.g., "201503123E" or mobile "+6591234567"
amount: amountToPay,
editable: false,
company: "Bill Splitter",
refNumber: "DINNER-123"
}).toString();

return (
<div>
<h3>Scan to Pay {userPhone}</h3>
<QRCodeCanvas value={qrPayload} size={200} />
<p>Amount: ${amountToPay.toFixed(2)}</p>
</div>
);
} 6. Suggested Development MilestonesPhase 1 (Core OCR Pipeline): Build the Node.js API endpoint to ingest an image file, run Tesseract.js, and output a JSON array via regex filtering. Build a basic React dropzone to preview the resulting JSON text so you can manually fix errors.Phase 2 (Session Management): Setup a database (or simple JSON/in-memory store for prototyping) to save session states so users visiting via a shared link (/split/:id) load the exact same bill item list.Phase 3 (Interactive Splitting & Settlement): Implement the participant UI for claiming items, calculate proportional tax/discounts automatically, and integrate the PayNow QR generator with payment checkboxes.
