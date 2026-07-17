from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.database.session import get_db
from app.models.campaign import Campaign
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.call import CampaignCreate, CampaignResponse

router = APIRouter(prefix="/api/campaign", tags=["Campaigns"])


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    repo = BaseRepository(Campaign, db)
    return await repo.create(**payload.model_dump())


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    repo = BaseRepository(Campaign, db)
    return await repo.list()
