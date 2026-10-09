from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UpdateStudentRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)


class UpdateStatusRequest(BaseModel):
    """Shared by the student (T23) and editor (T24) status endpoints — same
    shape either way."""

    status: Literal["ACTIVE", "INACTIVE", "LOCKED"]


class UpdateStudentVipRequest(BaseModel):
    is_vip: bool
    # Ignored when is_vip=False. Null with is_vip=True means "no expiry set
    # yet" — the normal path still sets this from the payment flow (T26).
    vip_expired_at: datetime | None = None


class CreateEditorRequest(BaseModel):
    email: EmailStr
    # 72 bytes is bcrypt's hard limit — see pbl6_common.security.
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=200)


class UpdateEditorRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)
