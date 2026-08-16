import uuid

import pytest
from pydantic import ValidationError

from app.schemas.claim import ClaimItemRequest, CreateClaimsRequest, DeleteClaimRequest


class TestCreateClaimsRequest:
    def test_valid_request(self):
        req = CreateClaimsRequest(
            participantName="Alice",
            claims=[ClaimItemRequest(itemId=uuid.uuid4(), quantity=1)],
        )
        assert req.participantName == "Alice"
        assert req.claims[0].quantity == 1

    def test_empty_participant_name_rejected(self):
        with pytest.raises(ValidationError):
            CreateClaimsRequest(
                participantName="",
                claims=[ClaimItemRequest(itemId=uuid.uuid4(), quantity=1)],
            )

    def test_zero_quantity_rejected(self):
        with pytest.raises(ValidationError):
            CreateClaimsRequest(
                participantName="Alice",
                claims=[ClaimItemRequest(itemId=uuid.uuid4(), quantity=0)],
            )

    def test_negative_quantity_rejected(self):
        with pytest.raises(ValidationError):
            CreateClaimsRequest(
                participantName="Alice",
                claims=[ClaimItemRequest(itemId=uuid.uuid4(), quantity=-1)],
            )

    def test_empty_claims_list_rejected(self):
        with pytest.raises(ValidationError):
            CreateClaimsRequest(
                participantName="Alice",
                claims=[],
            )


class TestDeleteClaimRequest:
    def test_valid_request(self):
        req = DeleteClaimRequest(participantName="Alice", itemId=uuid.uuid4())
        assert req.participantName == "Alice"

    def test_empty_participant_name_rejected(self):
        with pytest.raises(ValidationError):
            DeleteClaimRequest(participantName="", itemId=uuid.uuid4())
