from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.database.session import get_db
from app.models.customer import Customer
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.call import CustomerCreate, CustomerResponse

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    repo = BaseRepository(Customer, db)
    return await repo.create(**payload.model_dump())


@router.get("", response_model=list[CustomerResponse])
async def list_customers(
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    repo = BaseRepository(Customer, db)
    return await repo.list(limit=limit, offset=offset)
