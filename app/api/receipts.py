from fastapi import APIRouter, HTTPException, UploadFile

from app.schemas.receipt import ParsedReceipt
from app.services.ocr import ocr_service
from app.services.receipt_parser import parse_receipt_words

router = APIRouter(prefix="/api/receipts")

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_TYPES = {"image/jpeg", "image/png"}


@router.post("/parse", response_model=ParsedReceipt)
async def parse_receipt(image: UploadFile):
    # Validate file type
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG and PNG images are accepted")

    # Read and validate size
    contents = await image.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File size exceeds 10MB limit")

    # Run OCR
    if ocr_service.model is None:
        raise HTTPException(status_code=503, detail="OCR model not available")

    words = ocr_service.extract_words(contents)

    # Parse
    result = parse_receipt_words(words)

    return result
