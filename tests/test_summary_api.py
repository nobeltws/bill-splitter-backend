import uuid
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


SESSION_PAYLOAD = {
    "hostPaynowId": "+6591234567",
    "items": [
        {"name": "Chicken Rice", "quantity": 2, "unitPrice": 6.50},
        {"name": "Teh Tarik", "quantity": 1, "unitPrice": 2.00},
    ],
    "tax": 1.20,
    "serviceCharge": 2.00,
    "discount": 0,
    "participantCount": 2,
}


class TestGetSummary:
    async def test_summary_returns_200_with_claims(self, client):
        # Create session
        resp = await client.post("/api/sessions", json=SESSION_PAYLOAD)
        session_id = resp.json()["sessionId"]

        # Get items
        session_resp = await client.get(f"/api/sessions/{session_id}")
        items = session_resp.json()["items"]
        chicken_id = items[0]["id"]
        teh_id = items[1]["id"]

        # Create claims
        await client.post(
            f"/api/sessions/{session_id}/claims",
            json={
                "participantName": "Alice",
                "claims": [
                    {"itemId": chicken_id, "quantity": 1},
                    {"itemId": teh_id, "quantity": 1},
                ],
            },
        )
        await client.post(
            f"/api/sessions/{session_id}/claims",
            json={
                "participantName": "Bob",
                "claims": [{"itemId": chicken_id, "quantity": 1}],
            },
        )

        # Get summary
        response = await client.get(f"/api/sessions/{session_id}/summary")
        assert response.status_code == 200
        data = response.json()

        assert data["rawSubtotal"] == 15.00
        assert data["tax"] == 1.20
        assert data["serviceCharge"] == 2.00
        assert data["discount"] == 0
        assert data["grandTotal"] == 18.20

        participants = {p["name"]: p for p in data["participants"]}
        assert "Alice" in participants
        assert "Bob" in participants

        alice = participants["Alice"]
        assert alice["itemsSubtotal"] == 8.50
        assert alice["totalOwed"] > 0

        bob = participants["Bob"]
        assert bob["itemsSubtotal"] == 6.50
        assert bob["totalOwed"] > 0

    async def test_summary_not_found_returns_404(self, client):
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/sessions/{fake_id}/summary")
        assert response.status_code == 404

    async def test_summary_no_claims_shows_all_unclaimed(self, client):
        resp = await client.post("/api/sessions", json=SESSION_PAYLOAD)
        session_id = resp.json()["sessionId"]

        response = await client.get(f"/api/sessions/{session_id}/summary")
        assert response.status_code == 200
        data = response.json()

        assert data["participants"] == []
        assert data["unclaimed"]["subtotal"] == 15.00
        assert len(data["unclaimed"]["items"]) == 2
