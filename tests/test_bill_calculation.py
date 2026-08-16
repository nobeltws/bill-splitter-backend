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

    def test_two_participants_proportional_split(self):
        items = [
            {"quantity": 2, "unit_price": Decimal("10.00")},
            {"quantity": 1, "unit_price": Decimal("5.00")},
        ]
        claims = [
            {"participant_name": "Alice", "item_index": 0, "claimed_quantity": 1},
            {"participant_name": "Bob", "item_index": 0, "claimed_quantity": 1},
            {"participant_name": "Bob", "item_index": 1, "claimed_quantity": 1},
        ]
        result = BillCalculationService.calculate(
            items=items,
            claims=claims,
            tax=Decimal("2.50"),
            service_charge=Decimal("2.50"),
            discount=Decimal("0"),
            participant_count=2,
        )
        assert result["raw_subtotal"] == Decimal("25.00")
        assert result["grand_total"] == Decimal("30.00")

        alice = next(p for p in result["participants"] if p["name"] == "Alice")
        bob = next(p for p in result["participants"] if p["name"] == "Bob")

        assert alice["items_subtotal"] == Decimal("10.00")
        assert alice["proportional_tax"] == Decimal("1.00")
        assert alice["proportional_service_charge"] == Decimal("1.00")
        assert alice["total_owed"] == Decimal("12.00")

        assert bob["items_subtotal"] == Decimal("15.00")
        assert bob["proportional_tax"] == Decimal("1.50")
        assert bob["proportional_service_charge"] == Decimal("1.50")
        assert bob["total_owed"] == Decimal("18.00")

    def test_unclaimed_items_reported(self):
        items = [
            {"quantity": 2, "unit_price": Decimal("10.00")},
            {"quantity": 1, "unit_price": Decimal("5.00")},
        ]
        claims = [
            {"participant_name": "Alice", "item_index": 0, "claimed_quantity": 1},
        ]
        result = BillCalculationService.calculate(
            items=items,
            claims=claims,
            tax=Decimal("0"),
            service_charge=Decimal("0"),
            discount=Decimal("0"),
            participant_count=2,
        )
        assert result["unclaimed_subtotal"] == Decimal("15.00")
        alice = result["participants"][0]
        assert alice["items_subtotal"] == Decimal("10.00")
        assert alice["total_owed"] == Decimal("10.00")

    def test_zero_subtotal_returns_zero_proportionals(self):
        items = []
        claims = []
        result = BillCalculationService.calculate(
            items=items,
            claims=claims,
            tax=Decimal("0"),
            service_charge=Decimal("0"),
            discount=Decimal("0"),
            participant_count=1,
        )
        assert result["raw_subtotal"] == Decimal("0.00")
        assert result["grand_total"] == Decimal("0.00")
        assert result["participants"] == []

    def test_discount_exceeds_subtotal_caps_at_zero(self):
        items = [{"quantity": 1, "unit_price": Decimal("10.00")}]
        claims = [{"participant_name": "Alice", "item_index": 0, "claimed_quantity": 1}]
        result = BillCalculationService.calculate(
            items=items,
            claims=claims,
            tax=Decimal("1.00"),
            service_charge=Decimal("1.00"),
            discount=Decimal("50.00"),
            participant_count=1,
        )
        # grand_total should not go negative: 10 + 1 + 1 - 50 = -38 → capped at 0
        assert result["grand_total"] == Decimal("0.00")
        alice = result["participants"][0]
        assert alice["total_owed"] == Decimal("0.00")

    def test_rounding_adjustment_applied_to_largest_share(self):
        items = [{"quantity": 3, "unit_price": Decimal("10.00")}]
        claims = [
            {"participant_name": "Alice", "item_index": 0, "claimed_quantity": 1},
            {"participant_name": "Bob", "item_index": 0, "claimed_quantity": 1},
            {"participant_name": "Charlie", "item_index": 0, "claimed_quantity": 1},
        ]
        result = BillCalculationService.calculate(
            items=items,
            claims=claims,
            tax=Decimal("1.00"),
            service_charge=Decimal("0"),
            discount=Decimal("0"),
            participant_count=3,
        )
        # Grand total = 31.00, each share = 10.33... → 10.33 * 3 = 30.99
        # Rounding adjustment: largest share gets +0.01
        total_sum = sum(p["total_owed"] for p in result["participants"])
        assert total_sum == result["grand_total"]
