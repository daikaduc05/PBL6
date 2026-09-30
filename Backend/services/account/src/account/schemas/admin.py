from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class UpdateStudentRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=200)


class UpdateStudentStatusRequest(BaseModel):
    status: Literal["ACTIVE", "INACTIVE", "LOCKED"]


class UpdateStudentVipRequest(BaseModel):
    is_vip: bool
    # Ignored when is_vip=False. Null with is_vip=True means "no expiry set
    # yet" — the normal path still sets this from the payment flow (T26).
    vip_expired_at: datetime | None = None
