
from app.database import Base, get_session


def test_base_has_metadata():
    assert Base.metadata is not None


async def test_get_session_yields_async_session(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/testdb")

    gen = get_session()
    # get_session is an async generator — we can't fully test it without a real DB
    # but we verify it's an async generator function
    assert hasattr(gen, "__anext__")
    await gen.aclose()
