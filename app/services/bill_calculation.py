from decimal import Decimal, ROUND_HALF_EVEN

TWOPLACES = Decimal("0.01")


class BillCalculationService:
    @staticmethod
    def calculate(
        items: list[dict],
        claims: list[dict],
        tax_rate: Decimal,
        service_charge_rate: Decimal,
        discount: Decimal,
        participant_count: int,
    ) -> dict:
        raw_subtotal = sum(
            (Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"])) for item in items),
            Decimal("0"),
        )

        service_charge = (service_charge_rate * raw_subtotal).quantize(TWOPLACES, rounding=ROUND_HALF_EVEN)
        tax = (tax_rate * (raw_subtotal + service_charge)).quantize(TWOPLACES, rounding=ROUND_HALF_EVEN)
        grand_total = max(
            (raw_subtotal + service_charge + tax - discount).quantize(TWOPLACES, rounding=ROUND_HALF_EVEN),
            Decimal("0.00"),
        )

        participant_subtotals: dict[str, Decimal] = {}
        for claim in claims:
            item = items[claim["item_index"]]
            item_total = Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"]))
            share = (Decimal(str(claim["claimed_quantity"])) / Decimal(str(item["quantity"]))) * item_total
            name = claim["participant_name"]
            participant_subtotals[name] = participant_subtotals.get(name, Decimal("0")) + share

        per_person_discount = (
            (discount / Decimal(str(participant_count))).quantize(TWOPLACES, rounding=ROUND_HALF_EVEN)
            if participant_count > 0 else Decimal("0")
        )

        participants = []
        for name, subtotal in participant_subtotals.items():
            participant_service = (service_charge_rate * subtotal).quantize(TWOPLACES, rounding=ROUND_HALF_EVEN)
            participant_tax = (tax_rate * (subtotal + participant_service)).quantize(TWOPLACES, rounding=ROUND_HALF_EVEN)
            total_owed = max(
                (subtotal + participant_service + participant_tax - per_person_discount).quantize(TWOPLACES, rounding=ROUND_HALF_EVEN),
                Decimal("0.00"),
            )
            participants.append({
                "name": name,
                "items_subtotal": subtotal.quantize(TWOPLACES, rounding=ROUND_HALF_EVEN),
                "proportional_tax": participant_tax,
                "proportional_service_charge": participant_service,
                "proportional_discount": per_person_discount,
                "total_owed": total_owed,
            })

        claimed_subtotal = sum(p["items_subtotal"] for p in participants)
        unclaimed_subtotal = (raw_subtotal - claimed_subtotal).quantize(TWOPLACES, rounding=ROUND_HALF_EVEN)

        # Rounding adjustment: apply difference to largest share
        total_owed_sum = sum(p["total_owed"] for p in participants)
        if participants and total_owed_sum != grand_total and unclaimed_subtotal == Decimal("0"):
            diff = grand_total - total_owed_sum
            largest = max(participants, key=lambda p: p["total_owed"])
            largest["total_owed"] += diff

        return {
            "raw_subtotal": raw_subtotal.quantize(TWOPLACES, rounding=ROUND_HALF_EVEN),
            "tax": tax,
            "service_charge": service_charge,
            "discount": discount.quantize(TWOPLACES, rounding=ROUND_HALF_EVEN),
            "grand_total": grand_total,
            "participants": participants,
            "unclaimed_subtotal": unclaimed_subtotal,
        }
