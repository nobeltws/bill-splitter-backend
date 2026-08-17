from decimal import Decimal

from app.services.bill_calculation import BillCalculationService


class TestCalculateShares:
    def test_single_participant_claims_all(self):
        """Items=15.00, svc=10%=1.50, tax=9% of 16.50=1.48, grand=17.98"""
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
            tax_rate=Decimal("0.09"),
            service_charge_rate=Decimal("0.10"),
            discount=Decimal("0"),
            participant_count=1,
        )
        assert result["raw_subtotal"] == Decimal("15.00")
        assert result["service_charge"] == Decimal("1.50")
        assert result["tax"] == Decimal("1.48")  # 9% of 16.50 = 1.485 → 1.48 (ROUND_HALF_EVEN: 8 is even)
        assert result["grand_total"] == Decimal("17.98")
        alice = result["participants"][0]
        assert alice["items_subtotal"] == Decimal("15.00")
        assert alice["proportional_service_charge"] == Decimal("1.50")
        assert alice["proportional_tax"] == Decimal("1.48")
        assert alice["total_owed"] == Decimal("17.98")

    def test_two_participants_equal_discount_split(self):
        """Discount is split equally regardless of items ordered."""
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
            tax_rate=Decimal("0.09"),
            service_charge_rate=Decimal("0.10"),
            discount=Decimal("5.00"),
            participant_count=2,
        )
        # Each person gets discount/2 = 2.50
        alice = next(p for p in result["participants"] if p["name"] == "Alice")
        bob = next(p for p in result["participants"] if p["name"] == "Bob")

        assert alice["proportional_discount"] == Decimal("2.50")
        assert bob["proportional_discount"] == Decimal("2.50")

        # Alice: subtotal=10, svc=1.00, tax=0.99(9% of 11), total=10+1+0.99-2.50=9.49
        assert alice["items_subtotal"] == Decimal("10.00")
        assert alice["proportional_service_charge"] == Decimal("1.00")
        assert alice["proportional_tax"] == Decimal("0.99")
        assert alice["total_owed"] == Decimal("9.49")

        # Bob: subtotal=15, svc=1.50, tax=1.48(9% of 16.50=1.485→1.48 ROUND_HALF_EVEN)
        # Base total=15+1.50+1.48-2.50=15.48; grand_total=24.98, sum=9.49+15.48=24.97 → rounding adj +0.01 to Bob
        assert bob["items_subtotal"] == Decimal("15.00")
        assert bob["proportional_service_charge"] == Decimal("1.50")
        assert bob["proportional_tax"] == Decimal("1.48")
        assert bob["total_owed"] == Decimal("15.49")  # after rounding adjustment

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
            tax_rate=Decimal("0.09"),
            service_charge_rate=Decimal("0.10"),
            discount=Decimal("0"),
            participant_count=2,
        )
        assert result["unclaimed_subtotal"] == Decimal("15.00")
        alice = result["participants"][0]
        assert alice["items_subtotal"] == Decimal("10.00")

    def test_zero_subtotal_returns_zero_proportionals(self):
        result = BillCalculationService.calculate(
            items=[],
            claims=[],
            tax_rate=Decimal("0.09"),
            service_charge_rate=Decimal("0.10"),
            discount=Decimal("0"),
            participant_count=1,
        )
        assert result["raw_subtotal"] == Decimal("0.00")
        assert result["service_charge"] == Decimal("0.00")
        assert result["tax"] == Decimal("0.00")
        assert result["grand_total"] == Decimal("0.00")
        assert result["participants"] == []

    def test_discount_exceeds_total_caps_at_zero(self):
        items = [{"quantity": 1, "unit_price": Decimal("10.00")}]
        claims = [{"participant_name": "Alice", "item_index": 0, "claimed_quantity": 1}]
        result = BillCalculationService.calculate(
            items=items,
            claims=claims,
            tax_rate=Decimal("0.09"),
            service_charge_rate=Decimal("0.10"),
            discount=Decimal("50.00"),
            participant_count=1,
        )
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
            tax_rate=Decimal("0.09"),
            service_charge_rate=Decimal("0.10"),
            discount=Decimal("0"),
            participant_count=3,
        )
        total_sum = sum(p["total_owed"] for p in result["participants"])
        assert total_sum == result["grand_total"]

    def test_no_tax_no_service_charge(self):
        """When rates are 0, only raw subtotal minus discount matters."""
        items = [{"quantity": 1, "unit_price": Decimal("20.00")}]
        claims = [{"participant_name": "Alice", "item_index": 0, "claimed_quantity": 1}]
        result = BillCalculationService.calculate(
            items=items,
            claims=claims,
            tax_rate=Decimal("0"),
            service_charge_rate=Decimal("0"),
            discount=Decimal("5.00"),
            participant_count=1,
        )
        assert result["service_charge"] == Decimal("0.00")
        assert result["tax"] == Decimal("0.00")
        assert result["grand_total"] == Decimal("15.00")
        alice = result["participants"][0]
        assert alice["total_owed"] == Decimal("15.00")
