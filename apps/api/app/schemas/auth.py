from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NonceRequest(BaseModel):
    address: str = Field(min_length=42, max_length=42)
    chain_id: int


class AuthChallengeResponse(BaseModel):
    address: str
    chain_id: int
    message: str
    expires_at: datetime


class VerifyRequest(BaseModel):
    address: str = Field(min_length=42, max_length=42)
    message: str = Field(min_length=20, max_length=4000)
    signature: str = Field(min_length=130, max_length=132)


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    address: str
    chain_id: int
    created_at: datetime
    last_login_at: datetime
