import pytest
from pydantic import ValidationError

from app.schemas.session import CreateSessionRequest, SessionItemRequest


class TestSessionItemRequest:
    def test_valid_item(self):
        item = SessionItemRequest(name="Chicken Rice", quantity=2, unitPrice=6.50)
        assert item.name == "Chicken Rice"
        assert item.quantity == 2
        assert item.unitPrice == 6.50

    def test_quantity_must_be_positive(self):
        with pytest.raises(ValidationError) as exc_info:
            SessionItemRequest(name="Rice", quantity=0, unitPrice=5.00)
        assert "greater than 0" in str(exc_info.value).lower()

    def test_unit_price_must_be_positive(self):
        with pytest.raises(ValidationError) as exc_info:
            SessionItemRequest(name="Rice", quantity=1, unitPrice=0)
        assert "greater than 0" in str(exc_info.value).lower()

    def test_name_required(self):
        with pytest.raises(ValidationError):
            SessionItemRequest(name="", quantity=1, unitPrice=5.00)


class TestCreateSessionRequest:
    def test_valid_request(self):
        req = CreateSessionRequest(
            hostPaynowId="+6591234567",
            items=[{"name": "Chicken Rice", "quantity": 2, "unitPrice": 6.50}],
            tax=1.20,
            serviceCharge=2.00,
            discount=0,
        )
        assert req.hostPaynowId == "+6591234567"
        assert len(req.items) == 1

    def test_items_cannot_be_empty(self):
        with pytest.raises(ValidationError) as exc_info:
            CreateSessionRequest(
                hostPaynowId="+6591234567",
                items=[],
                tax=0,
                serviceCharge=0,
                discount=0,
            )
        assert "at least 1" in str(exc_info.value).lower()

    def test_host_paynow_id_required(self):
        with pytest.raises(ValidationError):
            CreateSessionRequest(
                hostPaynowId="",
                items=[{"name": "Rice", "quantity": 1, "unitPrice": 5.00}],
                tax=0,
                serviceCharge=0,
                discount=0,
            )

    def test_tax_defaults_to_zero(self):
        req = CreateSessionRequest(
            hostPaynowId="+6591234567",
            items=[{"name": "Rice", "quantity": 1, "unitPrice": 5.00}],
        )
        assert req.tax == 0
        assert req.serviceCharge == 0
        assert req.discount == 0
