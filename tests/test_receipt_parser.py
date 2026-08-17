from app.services.receipt_parser import parse_receipt_words


def _make_word(text, x_min, y_min, x_max, y_max, confidence=0.95):
    return {"text": text, "bbox": [x_min, y_min, x_max, y_max], "confidence": confidence}


def test_simple_item_extraction():
    words = [
        _make_word("Chicken", 0.05, 0.10, 0.20, 0.13),
        _make_word("Rice", 0.22, 0.10, 0.35, 0.13),
        _make_word("$6.50", 0.75, 0.10, 0.90, 0.13),
    ]
    result = parse_receipt_words(words)
    assert len(result.items) == 1
    assert result.items[0].name == "Chicken Rice"
    assert result.items[0].unitPrice == 6.50
    assert result.items[0].quantity == 1


def test_item_with_quantity():
    words = [
        _make_word("2", 0.05, 0.10, 0.08, 0.13),
        _make_word("Nasi", 0.10, 0.10, 0.20, 0.13),
        _make_word("Lemak", 0.22, 0.10, 0.35, 0.13),
        _make_word("$10.00", 0.75, 0.10, 0.90, 0.13),
    ]
    result = parse_receipt_words(words)
    assert len(result.items) == 1
    assert result.items[0].name == "Nasi Lemak"
    assert result.items[0].quantity == 2
    assert result.items[0].unitPrice == 5.00


def test_tax_extraction():
    words = [
        _make_word("7%", 0.05, 0.50, 0.12, 0.53),
        _make_word("GST", 0.14, 0.50, 0.25, 0.53),
        _make_word("$1.20", 0.75, 0.50, 0.90, 0.53),
    ]
    result = parse_receipt_words(words)
    assert result.tax == 1.20
    assert len(result.items) == 0


def test_service_charge_extraction():
    words = [
        _make_word("Service", 0.05, 0.55, 0.20, 0.58),
        _make_word("Charge", 0.22, 0.55, 0.38, 0.58),
        _make_word("$2.00", 0.75, 0.55, 0.90, 0.58),
    ]
    result = parse_receipt_words(words)
    assert result.serviceCharge == 2.00
    assert len(result.items) == 0


def test_blacklist_filtering():
    words = [
        _make_word("TOTAL", 0.05, 0.70, 0.20, 0.73),
        _make_word("$25.00", 0.75, 0.70, 0.90, 0.73),
    ]
    result = parse_receipt_words(words)
    assert len(result.items) == 0
    assert result.tax == 0
    assert result.serviceCharge == 0


def test_multiple_items():
    words = [
        # Line 1
        _make_word("Chicken", 0.05, 0.10, 0.20, 0.13),
        _make_word("Rice", 0.22, 0.10, 0.35, 0.13),
        _make_word("$6.50", 0.75, 0.10, 0.90, 0.13),
        # Line 2
        _make_word("Teh", 0.05, 0.16, 0.12, 0.19),
        _make_word("Tarik", 0.14, 0.16, 0.28, 0.19),
        _make_word("$1.80", 0.75, 0.16, 0.90, 0.19),
    ]
    result = parse_receipt_words(words)
    assert len(result.items) == 2
    assert result.items[0].name == "Chicken Rice"
    assert result.items[1].name == "Teh Tarik"


def test_raw_text_reconstruction():
    words = [
        _make_word("Hello", 0.05, 0.10, 0.20, 0.13),
        _make_word("World", 0.22, 0.10, 0.35, 0.13),
    ]
    result = parse_receipt_words(words)
    assert "Hello" in result.rawText
    assert "World" in result.rawText


def test_confidence_from_words():
    words = [
        _make_word("Roti", 0.05, 0.10, 0.15, 0.13, confidence=0.85),
        _make_word("Prata", 0.17, 0.10, 0.30, 0.13, confidence=0.90),
        _make_word("$2.00", 0.75, 0.10, 0.90, 0.13, confidence=0.95),
    ]
    result = parse_receipt_words(words)
    assert len(result.items) == 1
    assert result.items[0].confidence is not None
    assert result.items[0].confidence > 0


def test_price_on_separate_line_slight_y_offset():
    """Price word has a slightly different Y from item name (common in real receipts)."""
    words = [
        _make_word("1", 0.05, 0.100, 0.08, 0.130),
        _make_word("FISH&CHIPS", 0.10, 0.100, 0.40, 0.130),
        # Price is slightly higher (y offset of 0.005)
        _make_word("$26.00", 0.75, 0.095, 0.90, 0.125),
    ]
    result = parse_receipt_words(words)
    assert len(result.items) == 1
    assert result.items[0].name == "FISH&CHIPS"
    assert result.items[0].unitPrice == 26.00


def test_multiple_items_with_misaligned_prices():
    """Simulate a real receipt where prices are slightly offset from item names."""
    words = [
        # Item 1: GUNNER at y=0.30, price at y=0.30 (aligned)
        _make_word("1", 0.05, 0.30, 0.08, 0.33),
        _make_word("GUNNER", 0.10, 0.30, 0.30, 0.33),
        _make_word("$10.00", 0.75, 0.30, 0.90, 0.33),
        # Item 2: PEANUTS at y=0.35, price at y=0.35 (aligned)
        _make_word("1", 0.05, 0.35, 0.08, 0.38),
        _make_word("PEANUTS", 0.10, 0.35, 0.30, 0.38),
        _make_word("$3.00", 0.75, 0.35, 0.90, 0.38),
        # Item 3: STEAK AU POIVRE at y=0.40, price at y=0.40
        _make_word("1", 0.05, 0.40, 0.08, 0.43),
        _make_word("STEAK", 0.10, 0.40, 0.22, 0.43),
        _make_word("AU", 0.23, 0.40, 0.28, 0.43),
        _make_word("POIVRE", 0.29, 0.40, 0.42, 0.43),
        _make_word("$35.00", 0.75, 0.40, 0.90, 0.43),
    ]
    result = parse_receipt_words(words)
    assert len(result.items) == 3
    assert result.items[0].name == "GUNNER"
    assert result.items[0].unitPrice == 10.00
    assert result.items[1].name == "PEANUTS"
    assert result.items[1].unitPrice == 3.00
    assert result.items[2].name == "STEAK AU POIVRE"
    assert result.items[2].unitPrice == 35.00


def test_quantity_greater_than_one():
    """Item with quantity > 1 should divide total price by quantity."""
    words = [
        _make_word("3", 0.05, 0.50, 0.08, 0.53),
        _make_word("HH", 0.10, 0.50, 0.15, 0.53),
        _make_word("CARLSBERG", 0.16, 0.50, 0.35, 0.53),
        _make_word("$27.00", 0.75, 0.50, 0.90, 0.53),
    ]
    result = parse_receipt_words(words)
    assert len(result.items) == 1
    assert result.items[0].name == "HH CARLSBERG"
    assert result.items[0].quantity == 3
    assert result.items[0].unitPrice == 9.00


def test_full_receipt_simulation():
    """Simulate the Wala Wala receipt layout with all items."""
    words = [
        # CACHACA 51 GLS - $13.00
        _make_word("1", 0.05, 0.20, 0.08, 0.23),
        _make_word("CACHACA", 0.10, 0.20, 0.25, 0.23),
        _make_word("51", 0.26, 0.20, 0.30, 0.23),
        _make_word("GLS", 0.31, 0.20, 0.38, 0.23),
        _make_word("$13.00", 0.75, 0.20, 0.90, 0.23),
        # FISH&CHIPS - $26.00
        _make_word("1", 0.05, 0.25, 0.08, 0.28),
        _make_word("FISH&CHIPS", 0.10, 0.25, 0.35, 0.28),
        _make_word("$26.00", 0.75, 0.25, 0.90, 0.28),
        # GUNNER - $10.00
        _make_word("1", 0.05, 0.30, 0.08, 0.33),
        _make_word("GUNNER", 0.10, 0.30, 0.30, 0.33),
        _make_word("$10.00", 0.75, 0.30, 0.90, 0.33),
        # PEANUTS - $3.00
        _make_word("1", 0.05, 0.35, 0.08, 0.38),
        _make_word("PEANUTS", 0.10, 0.35, 0.30, 0.38),
        _make_word("$3.00", 0.75, 0.35, 0.90, 0.38),
        # STEAK AU POIVRE - $35.00
        _make_word("1", 0.05, 0.40, 0.08, 0.43),
        _make_word("STEAK", 0.10, 0.40, 0.20, 0.43),
        _make_word("AU", 0.21, 0.40, 0.26, 0.43),
        _make_word("POIVRE", 0.27, 0.40, 0.38, 0.43),
        _make_word("$35.00", 0.75, 0.40, 0.90, 0.43),
        # VIRGIN MOJITO - $10.00
        _make_word("1", 0.05, 0.45, 0.08, 0.48),
        _make_word("VIRGIN", 0.10, 0.45, 0.22, 0.48),
        _make_word("MOJITO", 0.23, 0.45, 0.38, 0.48),
        _make_word("$10.00", 0.75, 0.45, 0.90, 0.48),
        # 2 CHICKEN ASADO - $48.00
        _make_word("2", 0.05, 0.50, 0.08, 0.53),
        _make_word("CHICKEN", 0.10, 0.50, 0.25, 0.53),
        _make_word("ASADO", 0.26, 0.50, 0.38, 0.53),
        _make_word("$48.00", 0.75, 0.50, 0.90, 0.53),
        # CARLSBERG BTL - $13.00
        _make_word("1", 0.05, 0.55, 0.08, 0.58),
        _make_word("CARLSBERG", 0.10, 0.55, 0.30, 0.58),
        _make_word("BTL", 0.31, 0.55, 0.38, 0.58),
        _make_word("$13.00", 0.75, 0.55, 0.90, 0.58),
        # SUBTOTAL line (should be filtered by blacklist)
        _make_word("SUBTOTAL", 0.20, 0.75, 0.45, 0.78),
        _make_word("$248.00", 0.75, 0.75, 0.90, 0.78),
        # GST line
        _make_word("Inc.", 0.10, 0.80, 0.18, 0.83),
        _make_word("9%", 0.19, 0.80, 0.24, 0.83),
        _make_word("GST", 0.25, 0.80, 0.32, 0.83),
        _make_word("$20.48", 0.75, 0.80, 0.90, 0.83),
    ]
    result = parse_receipt_words(words)
    assert result.tax == 20.48
    assert len(result.items) == 8
    names = [item.name for item in result.items]
    assert "CACHACA 51 GLS" in names
    assert "FISH&CHIPS" in names
    assert "GUNNER" in names
    assert "PEANUTS" in names
    assert "STEAK AU POIVRE" in names
    assert "VIRGIN MOJITO" in names
    assert "CHICKEN ASADO" in names
    assert "CARLSBERG BTL" in names
    # Verify prices
    item_map = {item.name: item for item in result.items}
    assert item_map["GUNNER"].unitPrice == 10.00
    assert item_map["PEANUTS"].unitPrice == 3.00
    assert item_map["CHICKEN ASADO"].unitPrice == 24.00
    assert item_map["CHICKEN ASADO"].quantity == 2


def test_merged_line_with_multiple_prices_gets_split():
    """When OCR merges two items onto one line, the parser should detect and split."""
    words = [
        # Header line to establish receipt structure
        _make_word("TABLE:", 0.20, 0.05, 0.40, 0.08),
        _make_word("10", 0.42, 0.05, 0.48, 0.08),
        # Merged line: "1 GUNNER $10.00 $3.00" (GUNNER + PEANUTS' price)
        _make_word("1", 0.05, 0.30, 0.08, 0.33),
        _make_word("GUNNER", 0.10, 0.30, 0.30, 0.33),
        _make_word("$10.00", 0.70, 0.30, 0.82, 0.33),
        _make_word("$3.00", 0.83, 0.305, 0.92, 0.335),
        # PEANUTS on its own line (content only, its price is orphaned above)
        _make_word("1", 0.05, 0.35, 0.08, 0.38),
        _make_word("PEANUTS", 0.10, 0.35, 0.30, 0.38),
    ]
    result = parse_receipt_words(words)
    item_map = {item.name: item for item in result.items}
    assert "GUNNER" in item_map
    assert "PEANUTS" in item_map
    # GUNNER should get the rightmost price on its line ($3.00 or $10.00)
    # and PEANUTS should get matched via orphan matching
    total = sum(item.unitPrice * item.quantity for item in result.items)
    assert total == 13.00  # $10.00 + $3.00


def test_tax_on_separate_line_from_price():
    """When 'Inc. 9% GST' line doesn't have a price, find it on adjacent line."""
    words = [
        # Item
        _make_word("1", 0.05, 0.20, 0.08, 0.23),
        _make_word("Beer", 0.10, 0.20, 0.25, 0.23),
        _make_word("$10.00", 0.75, 0.20, 0.90, 0.23),
        # Subtotal + GST value on same line (as seen in real receipt)
        _make_word("SUBTOTAL", 0.20, 0.50, 0.45, 0.53),
        _make_word("$10.00", 0.70, 0.50, 0.82, 0.53),
        _make_word("$0.90", 0.83, 0.50, 0.92, 0.53),
        # GST label on next line (no price)
        _make_word("Inc.", 0.20, 0.55, 0.28, 0.58),
        _make_word("9%", 0.29, 0.55, 0.34, 0.58),
        _make_word("GST", 0.35, 0.55, 0.42, 0.58),
    ]
    result = parse_receipt_words(words)
    # Tax should be found from the adjacent line's price
    assert result.tax == 0.90


def test_header_and_footer_excluded_from_items():
    """Header text and footer text should not be treated as items."""
    words = [
        # Header
        _make_word("Wala", 0.30, 0.02, 0.40, 0.05),
        _make_word("Wala", 0.42, 0.02, 0.52, 0.05),
        _make_word("TABLE:", 0.30, 0.08, 0.42, 0.11),
        _make_word("10", 0.43, 0.08, 0.48, 0.11),
        # Items section
        _make_word("1", 0.05, 0.20, 0.08, 0.23),
        _make_word("Beer", 0.10, 0.20, 0.20, 0.23),
        _make_word("$10.00", 0.75, 0.20, 0.90, 0.23),
        _make_word("1", 0.05, 0.25, 0.08, 0.28),
        _make_word("Wine", 0.10, 0.25, 0.20, 0.28),
        _make_word("$15.00", 0.75, 0.25, 0.90, 0.28),
        # Footer
        _make_word("TOTAL", 0.20, 0.60, 0.35, 0.63),
        _make_word("$25.00", 0.75, 0.60, 0.90, 0.63),
        _make_word("Thank", 0.20, 0.70, 0.32, 0.73),
        _make_word("you", 0.33, 0.70, 0.40, 0.73),
    ]
    result = parse_receipt_words(words)
    assert len(result.items) == 2
    assert result.items[0].name == "Beer"
    assert result.items[0].unitPrice == 10.00
    assert result.items[1].name == "Wine"
    assert result.items[1].unitPrice == 15.00


def test_tight_line_spacing_with_price_y_offsets():
    """Simulate a receipt with tight line spacing and prices offset in Y.

    This models the real Wala Wala receipt where the lower portion has tight
    spacing and OCR places prices at slightly different Y from their items.
    Lines are spaced only 0.018 apart, and prices have Y-offsets of ~0.003.
    """
    words = [
        # Line 1: HH PINOT GRIGIO GLS - $10.00 (content at y=0.50, price at y=0.502)
        _make_word("1", 0.05, 0.500, 0.08, 0.514),
        _make_word("HH", 0.10, 0.500, 0.14, 0.514),
        _make_word("PINOT", 0.15, 0.500, 0.24, 0.514),
        _make_word("GRIGIO", 0.25, 0.500, 0.36, 0.514),
        _make_word("GLS", 0.37, 0.500, 0.42, 0.514),
        _make_word("$10.00", 0.75, 0.502, 0.90, 0.516),
        # Line 2: HH SAPPORO 50CL - $13.00 (content at y=0.520, price at y=0.522)
        _make_word("1", 0.05, 0.520, 0.08, 0.534),
        _make_word("HH", 0.10, 0.520, 0.14, 0.534),
        _make_word("SAPPORO", 0.15, 0.520, 0.28, 0.534),
        _make_word("50CL", 0.29, 0.520, 0.36, 0.534),
        _make_word("$13.00", 0.75, 0.522, 0.90, 0.536),
        # Line 3: HH SAUV BLANC GLS - $10.00 (content at y=0.540, price at y=0.541)
        _make_word("1", 0.05, 0.540, 0.08, 0.554),
        _make_word("HH", 0.10, 0.540, 0.14, 0.554),
        _make_word("SAUV", 0.15, 0.540, 0.22, 0.554),
        _make_word("BLANC", 0.23, 0.540, 0.32, 0.554),
        _make_word("GLS", 0.33, 0.540, 0.38, 0.554),
        _make_word("$10.00", 0.75, 0.541, 0.90, 0.555),
        # Line 4: MOSCOW MULE - $16.00
        _make_word("1", 0.05, 0.560, 0.08, 0.574),
        _make_word("MOSCOW", 0.10, 0.560, 0.22, 0.574),
        _make_word("MULE", 0.23, 0.560, 0.32, 0.574),
        _make_word("$16.00", 0.75, 0.560, 0.90, 0.574),
        # Line 5: NORDES GLS - $14.00
        _make_word("1", 0.05, 0.580, 0.08, 0.594),
        _make_word("NORDES", 0.10, 0.580, 0.22, 0.594),
        _make_word("GLS", 0.23, 0.580, 0.28, 0.594),
        _make_word("$14.00", 0.75, 0.580, 0.90, 0.594),
        # Line 6: 3 HH CARLSBERG - $27.00
        _make_word("3", 0.05, 0.600, 0.08, 0.614),
        _make_word("HH", 0.10, 0.600, 0.14, 0.614),
        _make_word("CARLSBERG", 0.15, 0.600, 0.32, 0.614),
        _make_word("$27.00", 0.75, 0.600, 0.90, 0.614),
    ]
    result = parse_receipt_words(words)
    assert len(result.items) == 6
    item_map = {item.name: item for item in result.items}
    assert "HH PINOT GRIGIO GLS" in item_map
    assert "HH SAPPORO 50CL" in item_map
    assert "HH SAUV BLANC GLS" in item_map
    assert "MOSCOW MULE" in item_map
    assert "NORDES GLS" in item_map
    assert "HH CARLSBERG" in item_map
    assert item_map["HH PINOT GRIGIO GLS"].unitPrice == 10.00
    assert item_map["HH SAPPORO 50CL"].unitPrice == 13.00
    assert item_map["HH SAUV BLANC GLS"].unitPrice == 10.00
    assert item_map["MOSCOW MULE"].unitPrice == 16.00
    assert item_map["NORDES GLS"].unitPrice == 14.00
    assert item_map["HH CARLSBERG"].unitPrice == 9.00
    assert item_map["HH CARLSBERG"].quantity == 3


def test_modification_lines_excluded_from_items():
    """Lines starting with * are item modifications and should not be items."""
    words = [
        # Item 1: Sanshoku Maguro Don - $32.80
        _make_word("1", 0.05, 0.30, 0.08, 0.33),
        _make_word("Sanshoku", 0.10, 0.30, 0.25, 0.33),
        _make_word("Maguro", 0.26, 0.30, 0.38, 0.33),
        _make_word("Don", 0.39, 0.30, 0.45, 0.33),
        _make_word("$32.80", 0.75, 0.30, 0.90, 0.33),
        # Modification: * 1 **No Spring Onion (no price)
        _make_word("*", 0.10, 0.34, 0.12, 0.37),
        _make_word("1", 0.13, 0.34, 0.15, 0.37),
        _make_word("**No", 0.16, 0.34, 0.22, 0.37),
        _make_word("Spring", 0.23, 0.34, 0.32, 0.37),
        _make_word("Onion", 0.33, 0.34, 0.42, 0.37),
        # Item 2: Natsumi Nabe - $11.80
        _make_word("1", 0.05, 0.38, 0.08, 0.41),
        _make_word("Natsumi", 0.10, 0.38, 0.22, 0.41),
        _make_word("Nabe", 0.23, 0.38, 0.32, 0.41),
        _make_word("$11.80", 0.75, 0.38, 0.90, 0.41),
        # Item 3: HKD Pork Belly Don - $12.80
        _make_word("1", 0.05, 0.42, 0.08, 0.45),
        _make_word("HKD", 0.10, 0.42, 0.16, 0.45),
        _make_word("Pork", 0.17, 0.42, 0.24, 0.45),
        _make_word("Belly", 0.25, 0.42, 0.33, 0.45),
        _make_word("Don", 0.34, 0.42, 0.40, 0.45),
        _make_word("$12.80", 0.75, 0.42, 0.90, 0.45),
        # Modification: * 1 **Less Sauce (no price)
        _make_word("*", 0.10, 0.46, 0.12, 0.49),
        _make_word("1", 0.13, 0.46, 0.15, 0.49),
        _make_word("**Less", 0.16, 0.46, 0.25, 0.49),
        _make_word("Sauce", 0.26, 0.46, 0.34, 0.49),
        # Item 4: Sushi Vinegar Rice - $2.00
        _make_word("1", 0.05, 0.50, 0.08, 0.53),
        _make_word("Sushi", 0.10, 0.50, 0.18, 0.53),
        _make_word("Vinegar", 0.19, 0.50, 0.30, 0.53),
        _make_word("Rice", 0.31, 0.50, 0.38, 0.53),
        _make_word("$2.00", 0.75, 0.50, 0.90, 0.53),
    ]
    result = parse_receipt_words(words)
    assert len(result.items) == 4
    item_map = {item.name: item for item in result.items}
    assert "Sanshoku Maguro Don" in item_map
    assert "Natsumi Nabe" in item_map
    assert "HKD Pork Belly Don" in item_map
    assert "Sushi Vinegar Rice" in item_map
    assert item_map["Sanshoku Maguro Don"].unitPrice == 32.80
    assert item_map["Natsumi Nabe"].unitPrice == 11.80
    assert item_map["HKD Pork Belly Don"].unitPrice == 12.80
    assert item_map["Sushi Vinegar Rice"].unitPrice == 2.00
