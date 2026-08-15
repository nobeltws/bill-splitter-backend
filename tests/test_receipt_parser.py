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
