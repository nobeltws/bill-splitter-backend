# app/services/session.py
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.repositories.session import SessionRepository
from app.services.bill_calculation import BillCalculationService


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
        participant_count: int,
    ) -> Session:
        return await self.repo.create(
            host_paynow_id=host_paynow_id,
            items=items,
            tax=Decimal(str(tax)),
            service_charge=Decimal(str(service_charge)),
            discount=Decimal(str(discount)),
            participant_count=participant_count,
        )

    async def get_session(self, session_id: uuid.UUID) -> Session | None:
        return await self.repo.get_by_id(session_id)

    async def get_summary(self, session_id: uuid.UUID) -> dict | None:
        session = await self.repo.get_by_id(session_id)
        if session is None:
            return None

        items = [
            {"quantity": item.quantity, "unit_price": item.unit_price}
            for item in session.items
        ]

        claims = []
        item_index_map = {item.id: i for i, item in enumerate(session.items)}
        for claim in session.claims:
            claims.append({
                "participant_name": claim.participant_name,
                "item_index": item_index_map[claim.item_id],
                "claimed_quantity": claim.quantity,
            })

        calc = BillCalculationService.calculate(
            items=items,
            claims=claims,
            tax=session.tax,
            service_charge=session.service_charge,
            discount=session.discount,
            participant_count=session.participant_count,
        )

        # Build unclaimed items list
        claimed_per_item: dict[int, int] = {}
        for claim in claims:
            idx = claim["item_index"]
            claimed_per_item[idx] = claimed_per_item.get(idx, 0) + claim["claimed_quantity"]

        unclaimed_items = []
        for i, item in enumerate(session.items):
            claimed_qty = claimed_per_item.get(i, 0)
            remaining = item.quantity - claimed_qty
            if remaining > 0:
                unclaimed_items.append({
                    "id": item.id,
                    "name": item.name,
                    "quantity": remaining,
                    "unitPrice": float(item.unit_price),
                })

        return {
            "rawSubtotal": float(calc["raw_subtotal"]),
            "tax": float(calc["tax"]),
            "serviceCharge": float(calc["service_charge"]),
            "discount": float(calc["discount"]),
            "grandTotal": float(calc["grand_total"]),
            "participants": [
                {
                    "name": p["name"],
                    "itemsSubtotal": float(p["items_subtotal"]),
                    "proportionalTax": float(p["proportional_tax"]),
                    "proportionalServiceCharge": float(p["proportional_service_charge"]),
                    "proportionalDiscount": float(p["proportional_discount"]),
                    "totalOwed": float(p["total_owed"]),
                }
                for p in calc["participants"]
            ],
            "unclaimed": {
                "items": unclaimed_items,
                "subtotal": float(calc["unclaimed_subtotal"]),
            },
        }
