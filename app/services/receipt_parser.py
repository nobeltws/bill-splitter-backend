import re

from app.schemas.receipt import ParsedItem, ParsedReceipt

BLACKLIST = [
    "total", "subtotal", "sub-total", "cash", "change",
    "visa", "mastercard", "amex", "nets", "balance",
    "thank you", "receipt", "invoice", "payment",
    "member", "points", "signature", "table",
    "pos", "rept#", "op:", "tel", "sts",
]

TAX_REGEX = re.compile(r"(\d+)%\s*(gst|tax|vat)", re.IGNORECASE)
SERVICE_CHARGE_REGEX = re.compile(
    r"(?:\d+%\s*)?(service\s*charge|svr?\s*ch(?:a?r)?g|svc)", re.IGNORECASE
)
PRICE_REGEX = re.compile(r"\$(\d+\.\d{1,2})")
QUANTITY_REGEX = re.compile(r"^(\d+)$")

Y_TOLERANCE = 0.01  # Words within this vertical distance are on the same line


def _filter_oversized_words(words: list[dict]) -> list[dict]:
    """Remove words with abnormally tall bounding boxes (OCR artifacts)."""
    if not words:
        return []

    heights = [w["bbox"][3] - w["bbox"][1] for w in words]
    heights.sort()
    median_height = heights[len(heights) // 2]

    max_height = median_height * 2.5
    return [w for w in words if (w["bbox"][3] - w["bbox"][1]) <= max_height]


def _cluster_into_lines(words: list[dict]) -> list[list[dict]]:
    if not words:
        return []

    words = _filter_oversized_words(words)
    if not words:
        return []

    sorted_words = sorted(words, key=lambda w: (w["bbox"][1], w["bbox"][0]))
    lines = []
    current_line = [sorted_words[0]]
    anchor_y = (sorted_words[0]["bbox"][1] + sorted_words[0]["bbox"][3]) / 2

    for word in sorted_words[1:]:
        y_center = (word["bbox"][1] + word["bbox"][3]) / 2

        if abs(y_center - anchor_y) <= Y_TOLERANCE:
            current_line.append(word)
        else:
            current_line.sort(key=lambda w: w["bbox"][0])
            lines.append(current_line)
            current_line = [word]
            anchor_y = y_center

    current_line.sort(key=lambda w: w["bbox"][0])
    lines.append(current_line)
    return lines


def _extract_price(line_text: str) -> float | None:
    matches = PRICE_REGEX.findall(line_text)
    if matches:
        return float(matches[-1])
    return None


def _is_blacklisted(line_text: str) -> bool:
    lower = line_text.lower()
    return any(word in lower for word in BLACKLIST)


def _line_confidence(line_words: list[dict]) -> float:
    confidences = [w["confidence"] for w in line_words if "confidence" in w]
    if not confidences:
        return 0.0
    return sum(confidences) / len(confidences)


def parse_receipt_words(words: list[dict]) -> ParsedReceipt:
    lines = _cluster_into_lines(words)

    items: list[ParsedItem] = []
    tax = 0.0
    service_charge = 0.0
    raw_lines: list[str] = []

    for line_words in lines:
        line_text = " ".join(w["text"] for w in line_words)
        raw_lines.append(line_text)

        # Check for tax
        if TAX_REGEX.search(line_text):
            price = _extract_price(line_text)
            if price is not None:
                tax = price
            continue

        # Check for service charge
        if SERVICE_CHARGE_REGEX.search(line_text):
            price = _extract_price(line_text)
            if price is not None:
                service_charge = price
            continue

        # Check blacklist
        if _is_blacklisted(line_text):
            continue

        # Try to extract item
        price = _extract_price(line_text)
        if price is None:
            continue

        # Extract quantity and name
        non_price_words = [w for w in line_words if not re.match(r"^\$\d+\.\d{1,2}$", w["text"])]
        quantity = 1
        name_words = []

        for w in non_price_words:
            if QUANTITY_REGEX.match(w["text"]) and not name_words:
                quantity = int(w["text"])
            else:
                name_words.append(w["text"])

        name = " ".join(name_words).strip()
        if not name:
            continue

        unit_price = round(price / quantity, 2)
        confidence = _line_confidence(line_words)

        if confidence < 0.9:
            continue

        items.append(
            ParsedItem(name=name, quantity=quantity, unitPrice=unit_price, confidence=confidence)
        )

    return ParsedReceipt(
        items=items,
        tax=tax,
        serviceCharge=service_charge,
        rawText="\n".join(raw_lines),
    )
