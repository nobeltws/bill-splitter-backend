from pydantic import BaseModel


class ParsedItem(BaseModel):
    name: str
    quantity: int
    unitPrice: float
    confidence: float | None = None


class WordBox(BaseModel):
    text: str
    bbox: list[float]
    confidence: float


class ParsedReceipt(BaseModel):
    items: list[ParsedItem]
    tax: float
    serviceCharge: float
    rawText: str
    wordBoxes: list[WordBox]
