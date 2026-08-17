import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.payment import PaymentRepository
from app.repositories.session import SessionRepository


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PaymentRepository(db)
        self.session_repo = SessionRepository(db)

    async def mark_paid(self, session_id: uuid.UUID, participant_name: str) -> dict:
        session = await self.session_repo.get_by_id(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        has_claims = await self.repo.participant_has_claims(session_id, participant_name)
        if not has_claims:
            raise HTTPException(
                status_code=400,
                detail=f"Participant '{participant_name}' has no claims in this session",
            )

        existing = await self.repo.get_payment(session_id, participant_name)
        if existing:
            return {
                "participant_name": existing.participant_name,
                "paid": True,
                "paid_at": existing.paid_at,
            }

        payment = await self.repo.create_payment(session_id, participant_name)
        await self.db.commit()
        return {
            "participant_name": payment.participant_name,
            "paid": True,
            "paid_at": payment.paid_at,
        }

    async def unmark_paid(self, session_id: uuid.UUID, participant_name: str) -> dict:
        session = await self.session_repo.get_by_id(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        deleted = await self.repo.delete_payment(session_id, participant_name)
        if not deleted:
            raise HTTPException(status_code=404, detail="Payment record not found")

        await self.db.commit()
        return {
            "participant_name": participant_name,
            "paid": False,
        }
