from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.core.constants import UserRole


class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    role: UserRole
    is_blocked: bool
    created_at: datetime

    model_config = {"from_attributes": True}
