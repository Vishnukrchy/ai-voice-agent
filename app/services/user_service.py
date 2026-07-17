from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, PasswordChangeRequest
from app.utils.logger import logger


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, data: UserCreate) -> User:
        # Check if email already exists
        result = await self.db.execute(select(User).where(User.email == data.email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
            is_active=True
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"User created: {user.email}")
        return user

    async def list_users(self, skip: int = 0, limit: int = 100) -> tuple[list[User], int]:
        # Get total count
        count_result = await self.db.execute(select(func.count()).select_from(User))
        total = count_result.scalar()
        
        # Get users with pagination
        result = await self.db.execute(
            select(User)
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        users = result.scalars().all()
        
        return list(users), total

    async def get_user(self, user_id: str) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user

    async def update_user(self, user_id: str, data: UserUpdate) -> User:
        user = await self.get_user(user_id)
        
        # Update fields if provided
        if data.email is not None:
            # Check if email is taken by another user
            result = await self.db.execute(
                select(User).where(User.email == data.email, User.id != user_id)
            )
            existing_user = result.scalar_one_or_none()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            user.email = data.email
        
        if data.full_name is not None:
            user.full_name = data.full_name
        
        if data.role is not None:
            user.role = data.role
        
        if data.is_active is not None:
            user.is_active = data.is_active
        
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"User updated: {user.email}")
        return user

    async def delete_user(self, user_id: str) -> None:
        user = await self.get_user(user_id)
        
        # Soft delete by deactivating
        user.is_active = False
        await self.db.commit()
        
        logger.info(f"User deactivated: {user.email}")

    async def change_password(
        self, 
        user_id: str, 
        data: PasswordChangeRequest,
        current_user: User
    ) -> None:
        # Users can only change their own password unless they are admin
        if user_id != current_user.id and current_user.role.value != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only change your own password"
            )
        
        user = await self.get_user(user_id)
        
        # Verify current password
        if not verify_password(data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        user.hashed_password = hash_password(data.new_password)
        await self.db.commit()
        
        logger.info(f"Password changed for user: {user.email}")
