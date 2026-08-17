from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PaymentRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    participantName: str = Field(min_length=1)


class PaymentResponse(BaseModel):
    participantName: str
    paid: bool
    paidAt: datetime | None = None


class SessionPaymentResponse(BaseModel):
    participantName: str
    paidAt: datetime
