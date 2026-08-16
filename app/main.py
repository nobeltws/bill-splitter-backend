import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.health import router as health_router
from app.api.receipts import router as receipts_router
from app.api.claims import router as claims_router
from app.api.sessions import router as sessions_router
from app.database import engine
from app.exceptions import register_exception_handlers
from app.services.ocr import ocr_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify DB connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        logger.warning("Database connection failed at startup", exc_info=True)

    # Load OCR model
    try:
        ocr_service.load_model()
    except Exception:
        logger.error("Failed to load OCR model", exc_info=True)

    yield
    await engine.dispose()


app = FastAPI(title="Bill Splitter", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health_router)
app.include_router(receipts_router)
app.include_router(sessions_router)
app.include_router(claims_router)
