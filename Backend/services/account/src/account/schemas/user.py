import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: str
    status: str
    is_vip: bool
    vip_expired_at: datetime | None
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)


class ChangePasswordRequest(BaseModel):
    current_password: str
    # 72 bytes is bcrypt's hard limit — see pbl6_common.security / schemas/auth.py.
    new_password: str = Field(min_length=8, max_length=72)
