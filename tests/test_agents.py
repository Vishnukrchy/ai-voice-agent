import pytest

from app.knowledge.chunker import chunk_text


def test_chunk_text_respects_size_and_overlap():
    text = "word " * 500  # 2500 chars
    chunks = chunk_text(text, chunk_size=800, overlap=150)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 800 + 20  # small tolerance for word-boundary snapping


def test_chunk_text_empty_input_returns_empty_list():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_text_short_input_returns_single_chunk():
    chunks = chunk_text("A short piece of text.", chunk_size=800, overlap=150)
    assert len(chunks) == 1
    assert chunks[0] == "A short piece of text."


@pytest.mark.asyncio
async def test_create_agent_requires_auth(client):
    response = await client.post(
        "/api/agents",
        json={
            "name": "Test Agent",
            "prompt": "Be helpful.",
            "greeting_message": "Hello!",
        },
    )
    assert response.status_code in (401, 403)
