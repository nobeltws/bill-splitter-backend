import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.payment import Payment


class PaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_payment(self, session_id: uuid.UUID, participant_name: str) -> Payment | None:
        stmt = select(Payment).where(
            Payment.session_id == session_id,
            Payment.participant_name == participant_name,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_payment(self, session_id: uuid.UUID, participant_name: str) -> Payment:
        payment = Payment(session_id=session_id, participant_name=participant_name)
        self.db.add(payment)
        await self.db.flush()
        return payment

    async def delete_payment(self, session_id: uuid.UUID, participant_name: str) -> bool:
        stmt = delete(Payment).where(
            Payment.session_id == session_id,
            Payment.participant_name == participant_name,
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def participant_has_claims(self, session_id: uuid.UUID, participant_name: str) -> bool:
        stmt = select(Claim.id).where(
            Claim.session_id == session_id,
            Claim.participant_name == participant_name,
        ).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
