import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.claim import (
    ClaimResponse,
    CreateClaimsRequest,
    CreateClaimsResponse,
    DeleteClaimRequest,
)
from app.services.claim import ClaimService

router = APIRouter(prefix="/api/sessions")


def get_service(db: AsyncSession = Depends(get_session)) -> ClaimService:
    return ClaimService(db)


@router.post("/{session_id}/claims", response_model=CreateClaimsResponse)
async def create_claims(
    session_id: uuid.UUID,
    body: CreateClaimsRequest,
    service: ClaimService = Depends(get_service),
):
    claims_data = [
        {"item_id": c.itemId, "quantity": c.quantity} for c in body.claims
    ]
    results = await service.create_claims(session_id, body.participantName, claims_data)
    return CreateClaimsResponse(
        participantName=body.participantName,
        claims=[
            ClaimResponse(itemId=r["item_id"], itemName=r["item_name"], quantity=r["quantity"])
            for r in results
        ],
    )


@router.delete("/{session_id}/claims")
async def delete_claim(
    session_id: uuid.UUID,
    body: DeleteClaimRequest,
    service: ClaimService = Depends(get_service),
):
    await service.delete_claim(session_id, body.participantName, body.itemId)
    return {"message": "Claim removed"}
