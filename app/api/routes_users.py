from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    PasswordChangeRequest,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user (public endpoint - no authentication required)."""
    return await UserService(db).create_user(data)


@router.get("", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all users (requires authentication)."""
    users, total = await UserService(db).list_users(skip=skip, limit=limit)
    return UserListResponse(users=users, total=total)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific user by ID (requires authentication)."""
    return await UserService(db).get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a user (requires authentication)."""
    return await UserService(db).update_user(user_id, data)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate/delete a user (requires authentication)."""
    await UserService(db).delete_user(user_id)


@router.patch("/{user_id}/password", status_code=204)
async def change_password(
    user_id: str,
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change user password (requires authentication)."""
    await UserService(db).change_password(user_id, data, current_user)
