import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SessionItemRequest(BaseModel):
    name: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unitPrice: float = Field(gt=0)


class CreateSessionRequest(BaseModel):
    hostPaynowId: str = Field(min_length=1)
    items: list[SessionItemRequest] = Field(min_length=1)
    tax: float = Field(default=0, ge=0)
    serviceCharge: float = Field(default=0, ge=0)
    discount: float = Field(default=0, ge=0)


class SessionItemResponse(BaseModel):
    id: uuid.UUID
    name: str
    quantity: int
    unitPrice: float

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_item(cls, item) -> "SessionItemResponse":
        return cls(
            id=item.id,
            name=item.name,
            quantity=item.quantity,
            unitPrice=float(item.unit_price),
        )


class CreateSessionResponse(BaseModel):
    sessionId: uuid.UUID
    createdAt: datetime


class GetSessionResponse(BaseModel):
    sessionId: uuid.UUID
    hostPaynowId: str
    items: list[SessionItemResponse]
    tax: float
    serviceCharge: float
    discount: float
    claims: list = []
    payments: list = []
    createdAt: datetime
