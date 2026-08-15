async def test_app_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_app_404_json(client):
    response = await client.get("/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Not Found"


async def test_openapi_docs_available(client):
    response = await client.get("/docs")
    assert response.status_code == 200
