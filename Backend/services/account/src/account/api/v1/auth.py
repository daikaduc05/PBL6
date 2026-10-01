"""T21 — HTTP layer only, no business logic (backend.md §3 layering rule).

POST /api/v1/auth/register   public
POST /api/v1/auth/login      public
POST /api/v1/auth/refresh    public
POST /api/v1/auth/logout     public (idempotent — revokes the given refresh token)
"""

from account.deps import get_auth_service
from account.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
)
from account.services.auth_service import AuthService
from fastapi import APIRouter, Depends, status

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
