from unittest.mock import patch

import pytest


@pytest.fixture
def mock_ocr_words():
    return [
        {"text": "Chicken", "bbox": [0.05, 0.10, 0.20, 0.13], "confidence": 0.95},
        {"text": "Rice", "bbox": [0.22, 0.10, 0.35, 0.13], "confidence": 0.93},
        {"text": "$6.50", "bbox": [0.75, 0.10, 0.90, 0.13], "confidence": 0.98},
        {"text": "7%", "bbox": [0.05, 0.50, 0.12, 0.53], "confidence": 0.90},
        {"text": "GST", "bbox": [0.14, 0.50, 0.25, 0.53], "confidence": 0.92},
        {"text": "$0.46", "bbox": [0.75, 0.50, 0.90, 0.53], "confidence": 0.97},
    ]


@patch("app.api.receipts.ocr_service")
async def test_parse_receipt_success(mock_ocr, client, mock_ocr_words):
    mock_ocr.model = "loaded"
    mock_ocr.extract_words.return_value = mock_ocr_words

    # Minimal valid JPEG bytes
    jpeg_bytes = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xd9"
    )

    response = await client.post(
        "/api/receipts/parse",
        files={"image": ("receipt.jpg", jpeg_bytes, "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["name"] == "Chicken Rice"
    assert body["items"][0]["unitPrice"] == 6.50
    assert body["tax"] == 0.46
    assert "rawText" in body


@patch("app.api.receipts.ocr_service")
async def test_parse_receipt_invalid_file_type(mock_ocr, client):
    mock_ocr.model = "loaded"

    response = await client.post(
        "/api/receipts/parse",
        files={"image": ("receipt.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 400


@patch("app.api.receipts.ocr_service")
async def test_parse_receipt_too_large(mock_ocr, client):
    mock_ocr.model = "loaded"

    large_file = b"\xff\xd8" + b"\x00" * (10 * 1024 * 1024 + 1)  # > 10MB

    response = await client.post(
        "/api/receipts/parse",
        files={"image": ("receipt.jpg", large_file, "image/jpeg")},
    )

    assert response.status_code == 413
