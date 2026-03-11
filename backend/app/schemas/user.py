from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    email: EmailStr
    timezone: str = Field(default="UTC")


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    timezone: str | None = None
    current_password: str | None = None
    password: str | None = Field(default=None, min_length=8)

    @field_validator("current_password")
    @classmethod
    def current_password_required_with_new(cls, v: str | None, info: object) -> str | None:
        # Validated at route level since we need the DB user; just pass through
        return v


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
