from datetime import datetime

from pydantic import BaseModel


class TokenPayload(BaseModel):
    sub: str
    exp: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
