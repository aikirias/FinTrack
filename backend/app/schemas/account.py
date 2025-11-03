from datetime import datetime

from pydantic import BaseModel, Field


class AccountBase(BaseModel):
    name: str = Field(max_length=100)
    currency_code: str = Field(pattern=r"^[A-Z]{3}$")
    description: str | None = Field(default=None, max_length=255)


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    currency_code: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    description: str | None = Field(default=None, max_length=255)
    is_archived: bool | None = None


class AccountOut(AccountBase):
    id: int
    is_default: bool
    is_archived: bool
    created_at: datetime

    class Config:
        from_attributes = True
