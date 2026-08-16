from decimal import Decimal

from app.services.bill_calculation import BillCalculationService


class TestCalculateShares:
    def test_single_participant_claims_all(self):
        items = [
            {"quantity": 2, "unit_price": Decimal("6.50")},
            {"quantity": 1, "unit_price": Decimal("2.00")},
        ]
        claims = [
            {"participant_name": "Alice", "item_index": 0, "claimed_quantity": 2},
            {"participant_name": "Alice", "item_index": 1, "claimed_quantity": 1},
        ]
        result = BillCalculationService.calculate(
            items=items,
            claims=claims,
            tax=Decimal("1.20"),
            service_charge=Decimal("2.00"),
            discount=Decimal("0"),
            participant_count=1,
        )
        assert result["raw_subtotal"] == Decimal("15.00")
        assert result["grand_total"] == Decimal("18.20")
        assert len(result["participants"]) == 1
        alice = result["participants"][0]
        assert alice["name"] == "Alice"
        assert alice["items_subtotal"] == Decimal("15.00")
        assert alice["total_owed"] == Decimal("18.20")
