"""T22 — HTTP layer only, no business logic (backend.md §3 layering rule).

    GET    /api/v1/users/me                 authenticated
    PATCH  /api/v1/users/me                 authenticated
    POST   /api/v1/users/me/change-password authenticated

"authenticated" means the gateway has verified the JWT and forwarded
X-User-Id (backend.md §7). There is no gateway yet (T08/T09), so until it
exists, set X-User-Id by hand when calling these directly — the same
interim gap backend.md already calls out for T09 depending on T21.
"""

import uuid

from account.deps import get_user_service
from account.schemas.user import ChangePasswordRequest, UpdateProfileRequest, UserProfileResponse
from account.services.user_service import UserService
from fastapi import APIRouter, Depends, status
from pbl6_common.deps import UserContext, get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfileResponse)
async def get_me(
    user: UserContext = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    return await svc.get_profile(uuid.UUID(user.user_id))


@router.patch("/me", response_model=UserProfileResponse)
async def update_me(
    body: UpdateProfileRequest,
    user: UserContext = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    return await svc.update_profile(uuid.UUID(user.user_id), full_name=body.full_name)


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePasswordRequest,
    user: UserContext = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    await svc.change_password(
        uuid.UUID(user.user_id),
        current_password=body.current_password,
        new_password=body.new_password,
    )
