from unittest.mock import MagicMock, patch

import pytest

from app.services.ocr import OCRService


def test_ocr_service_init_without_model():
    service = OCRService()
    assert service.model is None


def test_ocr_service_extract_words_requires_loaded_model():
    service = OCRService()
    with pytest.raises(RuntimeError, match="OCR model not loaded"):
        service.extract_words(b"fake image bytes")


@patch("app.services.ocr.OCRService._run_inference")
def test_ocr_service_extract_words_returns_word_list(mock_inference):
    mock_inference.return_value = [
        {"text": "Hello", "bbox": [0.1, 0.2, 0.3, 0.4], "confidence": 0.95},
        {"text": "World", "bbox": [0.5, 0.2, 0.7, 0.4], "confidence": 0.90},
    ]

    service = OCRService()
    service.model = MagicMock()  # pretend model is loaded

    result = service.extract_words(b"fake image bytes")

    assert len(result) == 2
    assert result[0]["text"] == "Hello"
    assert "bbox" in result[0]
    assert "confidence" in result[0]
