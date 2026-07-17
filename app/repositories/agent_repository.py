from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.repositories.base import BaseRepository


class AgentRepository(BaseRepository[Agent]):
    def __init__(self, db: AsyncSession):
        super().__init__(Agent, db)

    async def list_active(self, limit: int = 100, offset: int = 0) -> list[Agent]:
        result = await self.db.execute(
            select(Agent).where(Agent.is_active.is_(True)).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
