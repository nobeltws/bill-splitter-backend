import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


VALID_PAYLOAD = {
    "hostPaynowId": "+6591234567",
    "items": [
        {"name": "Chicken Rice", "quantity": 2, "unitPrice": 6.50},
        {"name": "Teh Tarik", "quantity": 1, "unitPrice": 2.00},
    ],
    "tax": 1.20,
    "serviceCharge": 2.00,
    "discount": 0,
}


class TestCreateSession:
    async def test_create_session_returns_201(self, client):
        response = await client.post("/api/sessions", json=VALID_PAYLOAD)
        assert response.status_code == 201
        data = response.json()
        assert "sessionId" in data
        assert "createdAt" in data
        uuid.UUID(data["sessionId"])

    async def test_create_session_empty_items_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "items": []}
        response = await client.post("/api/sessions", json=payload)
        assert response.status_code == 422

    async def test_create_session_invalid_quantity_returns_422(self, client):
        payload = {
            **VALID_PAYLOAD,
            "items": [{"name": "Rice", "quantity": 0, "unitPrice": 5.00}],
        }
        response = await client.post("/api/sessions", json=payload)
        assert response.status_code == 422

    async def test_create_session_missing_host_paynow_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "hostPaynowId": ""}
        response = await client.post("/api/sessions", json=payload)
        assert response.status_code == 422


class TestGetSession:
    async def test_get_session_returns_full_state(self, client):
        create_resp = await client.post("/api/sessions", json=VALID_PAYLOAD)
        session_id = create_resp.json()["sessionId"]

        response = await client.get(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["sessionId"] == session_id
        assert data["hostPaynowId"] == "+6591234567"
        assert len(data["items"]) == 2
        assert data["items"][0]["name"] == "Chicken Rice"
        assert data["items"][0]["quantity"] == 2
        assert data["items"][0]["unitPrice"] == 6.50
        assert data["tax"] == 1.20
        assert data["serviceCharge"] == 2.00
        assert data["discount"] == 0
        assert data["claims"] == []
        assert data["payments"] == []

    async def test_get_session_not_found_returns_404(self, client):
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/sessions/{fake_id}")
        assert response.status_code == 404

    async def test_get_session_invalid_uuid_returns_422(self, client):
        response = await client.get("/api/sessions/not-a-uuid")
        assert response.status_code == 422
