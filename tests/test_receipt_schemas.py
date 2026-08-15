from app.schemas.receipt import ParsedItem, ParsedReceipt, WordBox


def test_parsed_item_defaults():
    item = ParsedItem(name="Chicken Rice", quantity=2, unitPrice=6.50)
    assert item.confidence is None


def test_parsed_item_with_confidence():
    item = ParsedItem(name="Nasi Lemak", quantity=1, unitPrice=5.00, confidence=0.95)
    assert item.confidence == 0.95


def test_word_box():
    box = WordBox(text="Hello", bbox=[0.1, 0.2, 0.3, 0.4], confidence=0.99)
    assert box.text == "Hello"
    assert len(box.bbox) == 4


def test_parsed_receipt():
    receipt = ParsedReceipt(
        items=[ParsedItem(name="Item", quantity=1, unitPrice=10.0)],
        tax=0.70,
        serviceCharge=1.00,
        rawText="Item $10.00",
        wordBoxes=[],
    )
    assert receipt.tax == 0.70
    assert len(receipt.items) == 1
