"""T21 — HTTP layer only, no business logic (backend.md §3 layering rule).

POST /api/v1/auth/register         public
POST /api/v1/auth/login            public
POST /api/v1/auth/refresh          public
POST /api/v1/auth/logout           public (idempotent — revokes the given refresh token)
POST /api/v1/auth/forgot-password  public (always 204 — never reveals whether the email exists)
POST /api/v1/auth/reset-password   public (token from the emailed link)
"""

from fastapi import APIRouter, Depends, status

from account.deps import get_auth_service, get_password_reset_service
from account.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPairResponse,
)
from account.services.auth_service import AuthService
from account.services.password_reset_service import PasswordResetService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPairResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, auth: AuthService = Depends(get_auth_service)):
    user = await auth.register(email=body.email, password=body.password, full_name=body.full_name)
    return auth.issue_token_pair(user)


@router.post("/login", response_model=TokenPairResponse)
async def login(body: LoginRequest, auth: AuthService = Depends(get_auth_service)):
    user = await auth.authenticate(email=body.email, password=body.password)
    return auth.issue_token_pair(user)


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh(body: RefreshRequest, auth: AuthService = Depends(get_auth_service)):
    return await auth.refresh(body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: LogoutRequest, auth: AuthService = Depends(get_auth_service)):
    await auth.logout(body.refresh_token)


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(
    body: ForgotPasswordRequest,
    svc: PasswordResetService = Depends(get_password_reset_service),
):
    await svc.request_reset(body.email)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    body: ResetPasswordRequest,
    svc: PasswordResetService = Depends(get_password_reset_service),
):
    await svc.reset_password(token=body.token, new_password=body.new_password)
