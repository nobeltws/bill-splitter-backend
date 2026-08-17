import re

from app.schemas.receipt import ParsedItem, ParsedReceipt

BLACKLIST = [
    "total", "subtotal", "sub-total", "grand total", "cash", "change",
    "visa", "mastercard", "amex", "nets", "balance",
    "thank you", "receipt", "invoice", "payment",
    "member", "points", "signature", "table",
    "pos", "rept#", "op:", "tel", "sts",
    "gst", "service charge", "amount s$", "amount",
    "print bill", "come again", "patronizing", "dine in",
]

TAX_REGEX = re.compile(r"(\d+)%\s*(gst|tax|vat)", re.IGNORECASE)
SERVICE_CHARGE_REGEX = re.compile(
    r"(?:\d+%\s*)?(service\s*charge|svr?\s*ch(?:a?r)?g|svc)", re.IGNORECASE
)
PRICE_REGEX = re.compile(r"\$?(\d+\.\d{1,2})")
PRICE_WORD_REGEX = re.compile(r"^\$?\d+\.\d{1,2}$")
QUANTITY_REGEX = re.compile(r"^(\d+)$")
TAX_STANDALONE_REGEX = re.compile(r"\b(gst|tax|vat)\b", re.IGNORECASE)
MODIFICATION_REGEX = re.compile(r"^\*\s*\d*\s*\*{0,2}")


def _filter_oversized_words(words: list[dict]) -> list[dict]:
    if not words:
        return []
    heights = [w["bbox"][3] - w["bbox"][1] for w in words]
    heights.sort()
    median_height = heights[len(heights) // 2]
    max_height = median_height * 2.5
    return [w for w in words if (w["bbox"][3] - w["bbox"][1]) <= max_height]


def _y_center(word: dict) -> float:
    return (word["bbox"][1] + word["bbox"][3]) / 2


def _line_y_center(line_words: list[dict]) -> float:
    centers = [_y_center(w) for w in line_words]
    return sum(centers) / len(centers)


def _is_price_word(word: dict) -> bool:
    return bool(PRICE_WORD_REGEX.match(word["text"]))


def _is_modification_line(line_words: list[dict]) -> bool:
    text = " ".join(w["text"] for w in line_words)
    return bool(MODIFICATION_REGEX.match(text))


def _extract_price_value(text: str) -> float | None:
    matches = PRICE_REGEX.findall(text)
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


def _compute_content_tolerance(words: list[dict]) -> float:
    """Compute Y tolerance for clustering content words (no prices).

    Uses gap analysis to find the boundary between within-line variation
    and between-line gaps among content words only.
    """
    if len(words) < 2:
        return 0.01

    heights = sorted(w["bbox"][3] - w["bbox"][1] for w in words)
    median_height = heights[len(heights) // 2]

    y_centers = sorted(_y_center(w) for w in words)
    gaps = [y_centers[i + 1] - y_centers[i] for i in range(len(y_centers) - 1)]
    nonzero_gaps = sorted(g for g in gaps if g > 0.0005)

    if not nonzero_gaps:
        return median_height * 0.4

    # Find the first gap significantly larger than the running average
    running_sum = nonzero_gaps[0]
    for i in range(1, len(nonzero_gaps)):
        running_mean = running_sum / i
        if nonzero_gaps[i] > running_mean * 2.5:
            tolerance = nonzero_gaps[i - 1] * 1.3
            return max(min(tolerance, median_height * 0.7), 0.003)
        running_sum += nonzero_gaps[i]

    return max(median_height * 0.4, 0.003)


def _cluster_words_into_lines(words: list[dict], tolerance: float) -> list[list[dict]]:
    if not words:
        return []

    sorted_words = sorted(words, key=lambda w: (w["bbox"][1], w["bbox"][0]))
    lines: list[list[dict]] = []
    current_line = [sorted_words[0]]
    anchor_y = _y_center(sorted_words[0])

    for word in sorted_words[1:]:
        y_c = _y_center(word)
        if abs(y_c - anchor_y) <= tolerance:
            current_line.append(word)
        else:
            current_line.sort(key=lambda w: w["bbox"][0])
            lines.append(current_line)
            current_line = [word]
            anchor_y = y_c

    current_line.sort(key=lambda w: w["bbox"][0])
    lines.append(current_line)
    return lines


def _find_qty_column_x(content_words: list[dict]) -> float:
    """Find the X-boundary of the quantity column."""
    qty_candidates = [
        w for w in content_words
        if QUANTITY_REGEX.match(w["text"])
    ]
    if not qty_candidates:
        return 0.12
    x_mins = sorted(w["bbox"][0] for w in qty_candidates)
    idx = max(0, len(x_mins) // 4)
    return x_mins[idx] + 0.06


def _is_item_start(word: dict, qty_col_x: float) -> bool:
    """Check if a word is a quantity marker at the start of an item line."""
    return (
        QUANTITY_REGEX.match(word["text"]) is not None
        and word["bbox"][0] < qty_col_x
    )


def parse_receipt_words(words: list[dict]) -> ParsedReceipt:
    words = _filter_oversized_words(words)
    if not words:
        return ParsedReceipt(items=[], tax=0.0, serviceCharge=0.0, rawText="")

    # Separate price words from content words
    price_words: list[dict] = []
    content_words: list[dict] = []
    for w in words:
        if _is_price_word(w):
            price_words.append(w)
        else:
            content_words.append(w)

    # Cluster content words into lines (without prices interfering)
    tolerance = _compute_content_tolerance(content_words)
    content_lines = _cluster_words_into_lines(content_words, tolerance)

    # Build raw text from all words clustered together (for display)
    all_tolerance = _compute_content_tolerance(words)
    all_lines = _cluster_words_into_lines(words, all_tolerance)
    raw_lines = [" ".join(w["text"] for w in line) for line in all_lines]

    # Detect tax and service charge from all-word lines
    tax = 0.0
    service_charge = 0.0

    for idx, line_words in enumerate(all_lines):
        line_text = " ".join(w["text"] for w in line_words)
        if TAX_REGEX.search(line_text):
            price = _extract_price_value(line_text)
            if price is not None:
                tax = price
            else:
                # Look at neighboring lines for the tax amount
                for offset in [-1, 1]:
                    ni = idx + offset
                    if 0 <= ni < len(all_lines):
                        neighbor_text = " ".join(
                            w["text"] for w in all_lines[ni]
                        )
                        p = _extract_price_value(neighbor_text)
                        if p is not None and p < 100:
                            tax = p
                            break
        elif (TAX_STANDALONE_REGEX.search(line_text)
              and not SERVICE_CHARGE_REGEX.search(line_text)):
            price = _extract_price_value(line_text)
            if price is not None and price < 100:
                tax = price
            elif not price:
                for offset in [-1, 1]:
                    ni = idx + offset
                    if 0 <= ni < len(all_lines):
                        neighbor_text = " ".join(
                            w["text"] for w in all_lines[ni]
                        )
                        p = _extract_price_value(neighbor_text)
                        if p is not None and p < 100:
                            tax = p
                            break
        if SERVICE_CHARGE_REGEX.search(line_text):
            price = _extract_price_value(line_text)
            if price is not None:
                service_charge = price

    # Identify item lines from content clusters
    qty_col_x = _find_qty_column_x(content_words)
    heights = sorted(w["bbox"][3] - w["bbox"][1] for w in words)
    median_height = heights[len(heights) // 2]

    # Find content lines that start with a quantity marker (definite item starts)
    qty_line_indices = [
        i for i, line in enumerate(content_lines)
        if line and _is_item_start(line[0], qty_col_x)
    ]

    # Compute median line gap from content lines (used for merge decisions)
    median_line_gap = tolerance * 3
    if len(content_lines) >= 2:
        line_gaps = []
        for li in range(1, len(content_lines)):
            gap = (_line_y_center(content_lines[li])
                   - _line_y_center(content_lines[li - 1]))
            if gap > 0:
                line_gaps.append(gap)
        if line_gaps:
            line_gaps.sort()
            median_line_gap = line_gaps[len(line_gaps) // 2]

    if qty_line_indices:
        merge_threshold = median_line_gap * 0.4

        # Find item section end: first blacklisted line after last qty marker
        last_qty_idx = qty_line_indices[-1]
        item_section_end = len(content_lines)
        for j in range(last_qty_idx + 1, len(content_lines)):
            frag_text = " ".join(w["text"] for w in content_lines[j])
            if _is_blacklisted(frag_text):
                item_section_end = j
                break

        # Build item groups from qty-marked lines
        item_groups: list[list[dict]] = []

        for i in range(len(qty_line_indices)):
            idx = qty_line_indices[i]
            next_idx = (qty_line_indices[i + 1]
                        if i + 1 < len(qty_line_indices)
                        else item_section_end)

            group = list(content_lines[idx])
            group_yc = _line_y_center(group)

            for j in range(idx + 1, next_idx):
                frag = content_lines[j]
                frag_text = " ".join(w["text"] for w in frag)
                if _is_blacklisted(frag_text):
                    continue
                if _is_modification_line(frag):
                    continue
                frag_yc = _line_y_center(frag)

                if abs(frag_yc - group_yc) < merge_threshold:
                    group.extend(frag)
                else:
                    item_groups.append(group)
                    group = list(frag)
                    group_yc = _line_y_center(group)

            item_groups.append(group)

    else:
        # No qty markers — treat all non-blacklisted content lines as items
        item_groups = []
        for line in content_lines:
            line_text = " ".join(w["text"] for w in line)
            if _is_blacklisted(line_text):
                continue
            if _is_modification_line(line):
                continue
            item_groups.append(list(line))

    # Sort item groups by Y-center (top to bottom)
    item_groups.sort(key=lambda g: _line_y_center(g))

    # Remove groups that have no name (bare qty markers from OCR splits)
    def _group_has_name(group: list[dict]) -> bool:
        for w in group:
            if not (QUANTITY_REGEX.match(w["text"]) and w["bbox"][0] < qty_col_x):
                return True
        return False

    item_groups = [g for g in item_groups if _group_has_name(g)]

    # Filter prices to the item section (exclude header/footer prices)
    if item_groups:
        item_section_top = _line_y_center(item_groups[0])
        item_section_bottom = _line_y_center(item_groups[-1])
        margin = median_height * 3

        # Use item_section_end boundary if available (stronger than margin)
        if qty_line_indices and item_section_end < len(content_lines):
            footer_y = _line_y_center(content_lines[item_section_end])
            item_prices = [
                pw for pw in price_words
                if (item_section_top - margin) <= _y_center(pw) < footer_y
            ]
        else:
            item_prices = [
                pw for pw in price_words
                if (item_section_top - margin)
                <= _y_center(pw)
                <= (item_section_bottom + margin)
            ]
    else:
        item_prices = list(price_words)

    item_prices.sort(key=lambda w: _y_center(w))

    # Deduplicate prices at similar Y with same value (POS unit + total display)
    if len(item_prices) > 1:
        keep = [True] * len(item_prices)
        for i in range(len(item_prices) - 1):
            if not keep[i]:
                continue
            val_i = _extract_price_value(item_prices[i]["text"])
            for j in range(i + 1, len(item_prices)):
                if not keep[j]:
                    continue
                y_diff = abs(_y_center(item_prices[j]) - _y_center(item_prices[i]))
                if y_diff > median_height * 0.5:
                    break
                val_j = _extract_price_value(item_prices[j]["text"])
                if val_i is not None and val_j is not None and abs(val_i - val_j) < 0.02:
                    # Same value at same Y — keep rightmost (line total)
                    if item_prices[j]["bbox"][0] > item_prices[i]["bbox"][0]:
                        keep[i] = False
                    else:
                        keep[j] = False
        item_prices = [p for p, k in zip(item_prices, keep) if k]

    # If more item groups than prices, find which group to merge
    # by minimizing total Y-alignment error between groups and prices
    max_merges = 5
    while (len(item_groups) > len(item_prices)
           and len(item_groups) > 1
           and max_merges > 0):
        max_merges -= 1

        best_remove = None
        best_error = float("inf")

        for k in range(len(item_groups)):
            remaining = [g for i, g in enumerate(item_groups) if i != k]
            error = 0.0
            for i, g in enumerate(remaining):
                if i < len(item_prices):
                    error += abs(_line_y_center(g) - _y_center(item_prices[i]))
            if error < best_error:
                best_error = error
                best_remove = k

        if best_remove is None:
            break

        # Merge removed group into its nearest neighbor by Y
        removed = item_groups[best_remove]
        nearest_idx = None
        nearest_dist = float("inf")
        for i, g in enumerate(item_groups):
            if i == best_remove:
                continue
            dist = abs(_line_y_center(g) - _line_y_center(removed))
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_idx = i

        if nearest_idx is not None:
            item_groups[nearest_idx].extend(removed)
            item_groups[nearest_idx].sort(key=lambda w: w["bbox"][0])
        item_groups.pop(best_remove)

    # Match items to prices by vertical order (1st item ↔ 1st price, etc.)
    items: list[ParsedItem] = []
    price_idx = 0
    for group in item_groups:
        if price_idx >= len(item_prices):
            break

        # Extract quantity and name
        quantity = 1
        name_words: list[str] = []

        for w in group:
            if QUANTITY_REGEX.match(w["text"]) and not name_words:
                quantity = int(w["text"])
            else:
                name_words.append(w["text"])

        name = " ".join(name_words).strip()
        if not name or len(name) <= 1:
            continue

        price_word = item_prices[price_idx]
        price = _extract_price_value(price_word["text"])
        if price is None:
            price_idx += 1
            continue

        unit_price = round(price / quantity, 2)

        all_ws = group + [price_word]
        confidence = _line_confidence(all_ws)
        if confidence < 0.70:
            price_idx += 1
            continue

        price_idx += 1
        items.append(
            ParsedItem(
                name=name, quantity=quantity, unitPrice=unit_price, confidence=confidence
            )
        )

    return ParsedReceipt(
        items=items,
        tax=tax,
        serviceCharge=service_charge,
        rawText="\n".join(raw_lines),
    )
