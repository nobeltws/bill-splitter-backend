from pydantic import BaseModel


class ParsedItem(BaseModel):
    name: str
    quantity: int
    unitPrice: float
    confidence: float | None = None


class ParsedReceipt(BaseModel):
    items: list[ParsedItem]
    tax: float
    serviceCharge: float
    rawText: str
