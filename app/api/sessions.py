import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.claim import SessionClaimResponse
from app.schemas.session import (
    CreateSessionRequest,
    CreateSessionResponse,
    GetSessionResponse,
    SessionItemResponse,
)
from app.services.session import SessionService

router = APIRouter(prefix="/api/sessions")


def get_service(db: AsyncSession = Depends(get_session)) -> SessionService:
    return SessionService(db)


@router.post("", response_model=CreateSessionResponse, status_code=201)
async def create_session(
    body: CreateSessionRequest,
    service: SessionService = Depends(get_service),
):
    items = [
        {"name": item.name, "quantity": item.quantity, "unit_price": item.unitPrice}
        for item in body.items
    ]
    session = await service.create_session(
        host_paynow_id=body.hostPaynowId,
        items=items,
        tax=body.tax,
        service_charge=body.serviceCharge,
        discount=body.discount,
    )
    return CreateSessionResponse(sessionId=session.id, createdAt=session.created_at)


@router.get("/{session_id}", response_model=GetSessionResponse)
async def get_session_by_id(
    session_id: uuid.UUID,
    service: SessionService = Depends(get_service),
):
    session = await service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return GetSessionResponse(
        sessionId=session.id,
        hostPaynowId=session.host_paynow_id,
        items=[SessionItemResponse.from_orm_item(item) for item in session.items],
        tax=float(session.tax),
        serviceCharge=float(session.service_charge),
        discount=float(session.discount),
        claims=[
            SessionClaimResponse(
                participantName=claim.participant_name,
                itemId=claim.item_id,
                itemName=claim.item.name,
                quantity=claim.quantity,
            )
            for claim in session.claims
        ],
        payments=[],
        createdAt=session.created_at,
    )
