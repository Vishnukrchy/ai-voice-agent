from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import create_access_token
from app.auth.security import verify_password
from app.config import settings
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.utils.logger import logger


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(self, data: LoginRequest) -> TokenResponse:
        result = await self.db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if user is None or not verify_password(data.password, user.hashed_password):
            logger.warning(f"Failed login attempt for {data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

        token = create_access_token(subject=user.id, extra_claims={"role": user.role.value})
        logger.info(f"User {user.email} logged in")
        return TokenResponse(access_token=token, expires_in_hours=settings.jwt_expiration_hours)
