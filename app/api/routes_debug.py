"""
Debug-only route: lets you test an agent's knowledge retrieval + Gemini
reply logic directly over HTTP, without needing a live Twilio call.
Useful for verifying knowledge base grounding and prompt behavior in
isolation before wiring up real telephony.

Conversation history here is NOT persisted to the database — pass it back
in each request if you want multi-turn context, the same way you'd manage
state in a stateless chat client.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.database.session import get_db
from app.knowledge.chroma_client import query_knowledge
from app.llm.gemini_client import generate_reply
from app.services.agent_service import AgentService
from app.models.user import User

router = APIRouter(prefix="/api/debug", tags=["Debug"])


class ChatTurn(BaseModel):
    role: str  # "user" or "model"
    text: str


class TestChatRequest(BaseModel):
    message: str
    history: list[ChatTurn] = []


class TestChatResponse(BaseModel):
    reply: str
    context_chunks_used: list[str]
    knowledge_context_was_empty: bool


@router.post("/agents/{agent_id}/test-chat", response_model=TestChatResponse)
async def test_agent_chat(
    agent_id: str,
    payload: TestChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Send a single message to an agent and see exactly what knowledge
    chunks were retrieved and what Gemini replied — without a phone call."""
    agent = await AgentService(db).get_agent(agent_id)

    context_chunks = query_knowledge(agent_id, payload.message)
    knowledge_context = "\n---\n".join(context_chunks)

    reply = await generate_reply(
        system_prompt=agent.prompt,
        conversation_history=[{"role": t.role, "text": t.text} for t in payload.history],
        latest_user_text=payload.message,
        knowledge_context=knowledge_context,
        temperature=agent.temperature,
    )

    return TestChatResponse(
        reply=reply,
        context_chunks_used=context_chunks,
        knowledge_context_was_empty=len(context_chunks) == 0,
    )
