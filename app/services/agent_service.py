from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.repositories.agent_repository import AgentRepository
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentService:
    def __init__(self, db: AsyncSession):
        self.repo = AgentRepository(db)

    async def create_agent(self, data: AgentCreate, created_by: str) -> Agent:
        return await self.repo.create(**data.model_dump(), created_by=created_by)

    async def list_agents(self, limit: int = 100, offset: int = 0) -> list[Agent]:
        return await self.repo.list(limit=limit, offset=offset)

    async def get_agent(self, agent_id: str) -> Agent:
        agent = await self.repo.get(agent_id)
        if agent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        return agent

    async def update_agent(self, agent_id: str, data: AgentUpdate) -> Agent:
        agent = await self.get_agent(agent_id)
        return await self.repo.update(agent, **data.model_dump(exclude_unset=True))

    async def delete_agent(self, agent_id: str) -> None:
        agent = await self.get_agent(agent_id)
        deleted = await self.repo.delete(agent.id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete agent")
