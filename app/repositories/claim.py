import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim import Claim
from app.models.item import Item


class ClaimRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_claims_for_item(self, item_id: uuid.UUID) -> list[Claim]:
        stmt = select(Claim).where(Claim.item_id == item_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_existing_claim(
        self, session_id: uuid.UUID, item_id: uuid.UUID, participant_name: str
    ) -> Claim | None:
        stmt = select(Claim).where(
            Claim.session_id == session_id,
            Claim.item_id == item_id,
            Claim.participant_name == participant_name,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_claim(
        self, session_id: uuid.UUID, item_id: uuid.UUID, participant_name: str, quantity: int
    ) -> Claim:
        existing = await self.get_existing_claim(session_id, item_id, participant_name)
        if existing:
            existing.quantity = quantity
            claim = existing
        else:
            claim = Claim(
                session_id=session_id,
                item_id=item_id,
                participant_name=participant_name,
                quantity=quantity,
            )
            self.db.add(claim)
        await self.db.flush()
        return claim

    async def delete_claim(
        self, session_id: uuid.UUID, item_id: uuid.UUID, participant_name: str
    ) -> bool:
        stmt = delete(Claim).where(
            Claim.session_id == session_id,
            Claim.item_id == item_id,
            Claim.participant_name == participant_name,
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def get_item_with_session_check(
        self, item_id: uuid.UUID, session_id: uuid.UUID
    ) -> Item | None:
        stmt = select(Item).where(Item.id == item_id, Item.session_id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
