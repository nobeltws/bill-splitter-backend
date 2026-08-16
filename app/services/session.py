# app/services/session.py
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.repositories.session import SessionRepository


class SessionService:
    def __init__(self, db: AsyncSession):
        self.repo = SessionRepository(db)

    async def create_session(
        self,
        host_paynow_id: str,
        items: list[dict],
        tax: float,
        service_charge: float,
        discount: float,
    ) -> Session:
        return await self.repo.create(
            host_paynow_id=host_paynow_id,
            items=items,
            tax=Decimal(str(tax)),
            service_charge=Decimal(str(service_charge)),
            discount=Decimal(str(discount)),
        )

    async def get_session(self, session_id: uuid.UUID) -> Session | None:
        return await self.repo.get_by_id(session_id)
