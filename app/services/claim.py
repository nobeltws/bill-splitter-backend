import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.claim import ClaimRepository
from app.repositories.session import SessionRepository


class ClaimService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ClaimRepository(db)
        self.session_repo = SessionRepository(db)

    async def create_claims(
        self, session_id: uuid.UUID, participant_name: str, claims: list[dict]
    ) -> list[dict]:
        session = await self.session_repo.get_by_id(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        results = []
        for claim_data in claims:
            item_id = claim_data["item_id"]
            quantity = claim_data["quantity"]

            item = await self.repo.get_item_with_session_check(item_id, session_id)
            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Item {item_id} not found in this session",
                )

            existing_claims = await self.repo.get_claims_for_item(item_id)
            other_claimed = sum(
                c.quantity
                for c in existing_claims
                if c.participant_name != participant_name
            )
            if other_claimed + quantity > item.quantity:
                available = item.quantity - other_claimed
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot claim {quantity} of '{item.name}'. Only {available} available.",
                )

            await self.repo.upsert_claim(session_id, item_id, participant_name, quantity)
            results.append(
                {"item_id": item.id, "item_name": item.name, "quantity": quantity}
            )

        await self.db.commit()
        return results

    async def delete_claim(
        self, session_id: uuid.UUID, participant_name: str, item_id: uuid.UUID
    ) -> None:
        deleted = await self.repo.delete_claim(session_id, item_id, participant_name)
        if not deleted:
            raise HTTPException(status_code=404, detail="Claim not found")
        await self.db.commit()
