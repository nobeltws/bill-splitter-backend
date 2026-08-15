from unittest.mock import patch

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
@patch("app.main.ocr_service.load_model")
async def test_ocr_model_loaded_on_startup(mock_load):
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            pass

    mock_load.assert_called_once()
