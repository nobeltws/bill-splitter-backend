import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.payment import PaymentRequest, PaymentResponse
from app.services.payment import PaymentService

router = APIRouter(prefix="/api/sessions")


def get_service(db: AsyncSession = Depends(get_session)) -> PaymentService:
    return PaymentService(db)


@router.post("/{session_id}/payments", response_model=PaymentResponse)
async def mark_paid(
    session_id: uuid.UUID,
    body: PaymentRequest,
    service: PaymentService = Depends(get_service),
):
    result = await service.mark_paid(session_id, body.participantName)
    return PaymentResponse(
        participantName=result["participant_name"],
        paid=result["paid"],
        paidAt=result.get("paid_at"),
    )


@router.delete("/{session_id}/payments", response_model=PaymentResponse)
async def unmark_paid(
    session_id: uuid.UUID,
    body: PaymentRequest,
    service: PaymentService = Depends(get_service),
):
    result = await service.unmark_paid(session_id, body.participantName)
    return PaymentResponse(
        participantName=result["participant_name"],
        paid=result["paid"],
        paidAt=None,
    )
