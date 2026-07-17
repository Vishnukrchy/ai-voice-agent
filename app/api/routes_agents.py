from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.database.session import get_db
from app.models.user import User
from app.schemas.agent import AgentCreate, AgentResponse, AgentUpdate
from app.services.agent_service import AgentService

router = APIRouter(prefix="/api/agents", tags=["Agents"])


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    payload: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await AgentService(db).create_agent(payload, created_by=current_user.id)


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await AgentService(db).list_agents(limit=limit, offset=offset)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await AgentService(db).get_agent(agent_id)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    payload: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await AgentService(db).update_agent(agent_id, payload)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    await AgentService(db).delete_agent(agent_id)
