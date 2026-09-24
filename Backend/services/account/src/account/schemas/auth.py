from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    # 72 bytes is bcrypt's own hard limit (pbl6_common.security truncates
    # at the same boundary) — capped here so the API rejects an oversized
    # password with a clear 422 instead of silently truncating it.
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
