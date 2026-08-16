import uuid

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
}


async def create_session(client) -> dict:
    resp = await client.post("/api/sessions", json=SESSION_PAYLOAD)
    session_id = resp.json()["sessionId"]
    session_resp = await client.get(f"/api/sessions/{session_id}")
    return session_resp.json()


class TestCreateClaims:
    async def test_claim_single_item(self, client):
        session = await create_session(client)
        session_id = session["sessionId"]
        item_id = session["items"][0]["id"]

        response = await client.post(
            f"/api/sessions/{session_id}/claims",
            json={
                "participantName": "Alice",
                "claims": [{"itemId": item_id, "quantity": 1}],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["participantName"] == "Alice"
        assert len(data["claims"]) == 1
        assert data["claims"][0]["itemId"] == item_id
        assert data["claims"][0]["itemName"] == "Chicken Rice"
        assert data["claims"][0]["quantity"] == 1

    async def test_claim_shared_item(self, client):
        session = await create_session(client)
        session_id = session["sessionId"]
        item_id = session["items"][0]["id"]  # quantity=2

        await client.post(
            f"/api/sessions/{session_id}/claims",
            json={
                "participantName": "Alice",
                "claims": [{"itemId": item_id, "quantity": 1}],
            },
        )
        response = await client.post(
            f"/api/sessions/{session_id}/claims",
            json={
                "participantName": "Bob",
                "claims": [{"itemId": item_id, "quantity": 1}],
            },
        )
        assert response.status_code == 200
        assert response.json()["participantName"] == "Bob"

    async def test_overclaim_returns_400(self, client):
        session = await create_session(client)
        session_id = session["sessionId"]
        item_id = session["items"][1]["id"]  # Teh Tarik, quantity=1

        await client.post(
            f"/api/sessions/{session_id}/claims",
            json={
                "participantName": "Alice",
                "claims": [{"itemId": item_id, "quantity": 1}],
            },
        )
        response = await client.post(
            f"/api/sessions/{session_id}/claims",
            json={
                "participantName": "Bob",
                "claims": [{"itemId": item_id, "quantity": 1}],
            },
        )
        assert response.status_code == 400
        assert "available" in response.json()["detail"].lower()

    async def test_claim_nonexistent_item_returns_404(self, client):
        session = await create_session(client)
        session_id = session["sessionId"]

        response = await client.post(
            f"/api/sessions/{session_id}/claims",
            json={
                "participantName": "Alice",
                "claims": [{"itemId": str(uuid.uuid4()), "quantity": 1}],
            },
        )
        assert response.status_code == 404

    async def test_claim_zero_quantity_returns_422(self, client):
        session = await create_session(client)
        session_id = session["sessionId"]
        item_id = session["items"][0]["id"]

        response = await client.post(
            f"/api/sessions/{session_id}/claims",
            json={
                "participantName": "Alice",
                "claims": [{"itemId": item_id, "quantity": 0}],
            },
        )
        assert response.status_code == 422

    async def test_claim_negative_quantity_returns_422(self, client):
        session = await create_session(client)
        session_id = session["sessionId"]
        item_id = session["items"][0]["id"]

        response = await client.post(
            f"/api/sessions/{session_id}/claims",
            json={
                "participantName": "Alice",
                "claims": [{"itemId": item_id, "quantity": -1}],
            },
        )
        assert response.status_code == 422

    async def test_claim_empty_participant_returns_422(self, client):
        session = await create_session(client)
        session_id = session["sessionId"]
        item_id = session["items"][0]["id"]

        response = await client.post(
            f"/api/sessions/{session_id}/claims",
            json={
                "participantName": "",
                "claims": [{"itemId": item_id, "quantity": 1}],
            },
        )
        assert response.status_code == 422

    async def test_upsert_claim_updates_quantity(self, client):
        session = await create_session(client)
        session_id = session["sessionId"]
        item_id = session["items"][0]["id"]  # quantity=2

        await client.post(
            f"/api/sessions/{session_id}/claims",
            json={
                "participantName": "Alice",
                "claims": [{"itemId": item_id, "quantity": 1}],
            },
        )
        response = await client.post(
            f"/api/sessions/{session_id}/claims",
            json={
                "participantName": "Alice",
                "claims": [{"itemId": item_id, "quantity": 2}],
            },
        )
        assert response.status_code == 200
        assert response.json()["claims"][0]["quantity"] == 2

    async def test_claims_visible_in_get_session(self, client):
        session = await create_session(client)
        session_id = session["sessionId"]
        item_id = session["items"][0]["id"]

        await client.post(
            f"/api/sessions/{session_id}/claims",
            json={
                "participantName": "Alice",
                "claims": [{"itemId": item_id, "quantity": 1}],
            },
        )

        response = await client.get(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["claims"]) == 1
        assert data["claims"][0]["participantName"] == "Alice"
        assert data["claims"][0]["itemId"] == item_id
        assert data["claims"][0]["itemName"] == "Chicken Rice"
        assert data["claims"][0]["quantity"] == 1


class TestDeleteClaim:
    async def test_delete_existing_claim(self, client):
        session = await create_session(client)
        session_id = session["sessionId"]
        item_id = session["items"][0]["id"]

        await client.post(
            f"/api/sessions/{session_id}/claims",
            json={
                "participantName": "Alice",
                "claims": [{"itemId": item_id, "quantity": 1}],
            },
        )

        response = await client.request(
            "DELETE",
            f"/api/sessions/{session_id}/claims",
            json={"participantName": "Alice", "itemId": item_id},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Claim removed"

    async def test_delete_nonexistent_claim_returns_404(self, client):
        session = await create_session(client)
        session_id = session["sessionId"]
        item_id = session["items"][0]["id"]

        response = await client.request(
            "DELETE",
            f"/api/sessions/{session_id}/claims",
            json={"participantName": "Alice", "itemId": item_id},
        )
        assert response.status_code == 404

    async def test_deleted_claim_frees_quantity(self, client):
        session = await create_session(client)
        session_id = session["sessionId"]
        item_id = session["items"][1]["id"]  # Teh Tarik, quantity=1

        await client.post(
            f"/api/sessions/{session_id}/claims",
            json={
                "participantName": "Alice",
                "claims": [{"itemId": item_id, "quantity": 1}],
            },
        )

        await client.request(
            "DELETE",
            f"/api/sessions/{session_id}/claims",
            json={"participantName": "Alice", "itemId": item_id},
        )

        response = await client.post(
            f"/api/sessions/{session_id}/claims",
            json={
                "participantName": "Bob",
                "claims": [{"itemId": item_id, "quantity": 1}],
            },
        )
        assert response.status_code == 200
