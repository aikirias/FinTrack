from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    timezone: str = Field(default="UTC")


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    timezone: str | None = None
    password: str | None = Field(default=None, min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    timezone: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
