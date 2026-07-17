"""
Shared pytest fixtures. Tests run against a real MySQL test database
(set TEST_DATABASE_URL) rather than SQLite, since the app uses MySQL-specific
types (CHAR(36) PKs) that don't behave identically elsewhere.
"""
import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("TWILIO_ACCOUNT_SID", "test-sid")
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test-token")
os.environ.setdefault("TWILIO_PHONE_NUMBER", "+10000000000")
os.environ.setdefault("ELEVENLABS_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "mysql+aiomysql://root:changeme@localhost:3306/voice_agent_test")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest-only")


@pytest_asyncio.fixture
async def client():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
