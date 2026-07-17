from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.limiter import limiter
from app.database.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService(db).login(payload)
