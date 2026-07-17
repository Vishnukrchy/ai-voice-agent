"""Coordinates a single conversational turn: retrieve knowledge context,
call Gemini for the next reply, and persist the message. This is called
from the Media Streams WebSocket handler for each user utterance."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.chroma_client import query_knowledge
from app.llm.gemini_client import generate_reply
from app.models.agent import Agent
from app.models.conversation_message import ConversationMessage, Speaker
from app.utils.logger import logger


class ConversationOrchestrator:
    def __init__(self, db: AsyncSession, agent: Agent, call_id: str):
        self.db = db
        self.agent = agent
        self.call_id = call_id

    async def _load_history(self) -> list[dict]:
        from sqlalchemy import select
        result = await self.db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.call_id == self.call_id)
            .order_by(ConversationMessage.timestamp)
        )
        messages = result.scalars().all()
        return [
            {"role": "model" if m.speaker == Speaker.agent else "user", "text": m.message}
            for m in messages
            if m.speaker != Speaker.system
        ]

    async def _save_message(self, speaker: Speaker, text: str) -> None:
        self.db.add(ConversationMessage(call_id=self.call_id, speaker=speaker, message=text))
        await self.db.commit()

    async def handle_user_utterance(self, user_text: str) -> str:
        """Given the customer's transcribed speech, saves it, retrieves
        relevant knowledge, generates the agent's reply, saves it, and
        returns the reply text for TTS synthesis."""
        history_before = await self._load_history()  # prior turns only, before this utterance
        await self._save_message(Speaker.customer, user_text)

        context_chunks = query_knowledge(self.agent.id, user_text)
        knowledge_context = "\n---\n".join(context_chunks)

        reply = await generate_reply(
            system_prompt=self.agent.prompt,
            conversation_history=history_before,
            latest_user_text=user_text,
            knowledge_context=knowledge_context,
            temperature=self.agent.temperature,
        )

        await self._save_message(Speaker.agent, reply)
        logger.info(f"Call {self.call_id} | reply generated ({len(reply)} chars)")
        return reply

    async def send_greeting(self) -> str:
        await self._save_message(Speaker.agent, self.agent.greeting_message)
        return self.agent.greeting_message
