import uuid

from pydantic import BaseModel, ConfigDict, Field


class ClaimItemRequest(BaseModel):
    itemId: uuid.UUID
    quantity: int = Field(gt=0)


class CreateClaimsRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    participantName: str = Field(min_length=1)
    claims: list[ClaimItemRequest] = Field(min_length=1)


class DeleteClaimRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    participantName: str = Field(min_length=1)
    itemId: uuid.UUID


class ClaimResponse(BaseModel):
    itemId: uuid.UUID
    itemName: str
    quantity: int


class CreateClaimsResponse(BaseModel):
    participantName: str
    claims: list[ClaimResponse]


class SessionClaimResponse(BaseModel):
    participantName: str
    itemId: uuid.UUID
    itemName: str
    quantity: int
