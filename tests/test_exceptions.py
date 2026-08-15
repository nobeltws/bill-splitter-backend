from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.exceptions import register_exception_handlers


def test_404_returns_json():
    app = FastAPI()
    register_exception_handlers(app)

    client = TestClient(app)
    response = client.get("/nonexistent")

    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "Not Found"


def test_500_returns_json():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    async def boom():
        raise RuntimeError("unexpected")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/boom")

    assert response.status_code == 500
    body = response.json()
    assert body["detail"] == "Internal Server Error"
