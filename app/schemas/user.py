from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole = UserRole.admin


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)
