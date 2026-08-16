# app/repositories/session.py
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.claim import Claim
from app.models.item import Item
from app.models.session import Session


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        host_paynow_id: str,
        items: list[dict],
        tax: Decimal,
        service_charge: Decimal,
        discount: Decimal,
    ) -> Session:
        session = Session(
            host_paynow_id=host_paynow_id,
            tax=tax,
            service_charge=service_charge,
            discount=discount,
        )
        for item_data in items:
            item = Item(
                name=item_data["name"],
                quantity=item_data["quantity"],
                unit_price=Decimal(str(item_data["unit_price"])),
            )
            session.items.append(item)

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_by_id(self, session_id: uuid.UUID) -> Session | None:
        stmt = (
            select(Session)
            .options(selectinload(Session.items), selectinload(Session.claims).selectinload(Claim.item))
            .where(Session.id == session_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
