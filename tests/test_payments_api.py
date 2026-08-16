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
    "taxRate": 0.09,
    "serviceChargeRate": 0.10,
    "discount": 0,
}


async def create_session_with_claim(client) -> tuple[str, str]:
    """Create a session and have Alice claim an item. Returns (session_id, item_id)."""
    resp = await client.post("/api/sessions", json=SESSION_PAYLOAD)
    session_id = resp.json()["sessionId"]

    session_resp = await client.get(f"/api/sessions/{session_id}")
    item_id = session_resp.json()["items"][0]["id"]

    await client.post(
        f"/api/sessions/{session_id}/claims",
        json={
            "participantName": "Alice",
            "claims": [{"itemId": item_id, "quantity": 1}],
        },
    )
    return session_id, item_id


class TestMarkPaid:
    async def test_mark_paid_success(self, client):
        session_id, _ = await create_session_with_claim(client)

        response = await client.post(
            f"/api/sessions/{session_id}/payments",
            json={"participantName": "Alice"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["participantName"] == "Alice"
        assert data["paid"] is True
        assert data["paidAt"] is not None

    async def test_mark_paid_idempotent(self, client):
        session_id, _ = await create_session_with_claim(client)

        await client.post(
            f"/api/sessions/{session_id}/payments",
            json={"participantName": "Alice"},
        )
        response = await client.post(
            f"/api/sessions/{session_id}/payments",
            json={"participantName": "Alice"},
        )
        assert response.status_code == 200
        assert response.json()["paid"] is True

    async def test_mark_paid_no_claims_returns_400(self, client):
        resp = await client.post("/api/sessions", json=SESSION_PAYLOAD)
        session_id = resp.json()["sessionId"]

        response = await client.post(
            f"/api/sessions/{session_id}/payments",
            json={"participantName": "Bob"},
        )
        assert response.status_code == 400
        assert "no claims" in response.json()["detail"].lower()

    async def test_mark_paid_nonexistent_session_returns_404(self, client):
        response = await client.post(
            f"/api/sessions/{uuid.uuid4()}/payments",
            json={"participantName": "Alice"},
        )
        assert response.status_code == 404

    async def test_mark_paid_empty_name_returns_422(self, client):
        session_id, _ = await create_session_with_claim(client)

        response = await client.post(
            f"/api/sessions/{session_id}/payments",
            json={"participantName": ""},
        )
        assert response.status_code == 422


class TestUnmarkPaid:
    async def test_unmark_paid_success(self, client):
        session_id, _ = await create_session_with_claim(client)

        await client.post(
            f"/api/sessions/{session_id}/payments",
            json={"participantName": "Alice"},
        )
        response = await client.request(
            "DELETE",
            f"/api/sessions/{session_id}/payments",
            json={"participantName": "Alice"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["participantName"] == "Alice"
        assert data["paid"] is False
        assert data["paidAt"] is None

    async def test_unmark_paid_not_marked_returns_404(self, client):
        session_id, _ = await create_session_with_claim(client)

        response = await client.request(
            "DELETE",
            f"/api/sessions/{session_id}/payments",
            json={"participantName": "Alice"},
        )
        assert response.status_code == 404

    async def test_unmark_paid_nonexistent_session_returns_404(self, client):
        response = await client.request(
            "DELETE",
            f"/api/sessions/{uuid.uuid4()}/payments",
            json={"participantName": "Alice"},
        )
        assert response.status_code == 404


class TestPaymentInSessionGet:
    async def test_payment_visible_in_session_get(self, client):
        session_id, _ = await create_session_with_claim(client)

        await client.post(
            f"/api/sessions/{session_id}/payments",
            json={"participantName": "Alice"},
        )

        response = await client.get(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["payments"]) == 1
        assert data["payments"][0]["participantName"] == "Alice"
        assert data["payments"][0]["paidAt"] is not None

    async def test_no_payments_returns_empty_list(self, client):
        session_id, _ = await create_session_with_claim(client)

        response = await client.get(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["payments"] == []

    async def test_unmarked_payment_removed_from_session_get(self, client):
        session_id, _ = await create_session_with_claim(client)

        await client.post(
            f"/api/sessions/{session_id}/payments",
            json={"participantName": "Alice"},
        )
        await client.request(
            "DELETE",
            f"/api/sessions/{session_id}/payments",
            json={"participantName": "Alice"},
        )

        response = await client.get(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["payments"] == []
