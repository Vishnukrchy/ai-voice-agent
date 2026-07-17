from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_hours: int


class CurrentUser(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
