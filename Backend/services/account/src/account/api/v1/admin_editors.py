"""T24 — HTTP layer only, no business logic (backend.md §3 layering rule).

    POST   /api/v1/admin/editors               admin — create an editor account
    GET    /api/v1/admin/editors                admin — list, paginated
    GET    /api/v1/admin/editors/{id}           admin
    PATCH  /api/v1/admin/editors/{id}           admin — edit full_name
    PATCH  /api/v1/admin/editors/{id}/status    admin — ACTIVE / INACTIVE / LOCKED
    DELETE /api/v1/admin/editors/{id}           admin — soft delete

Same interim gap as T22/T23: no gateway yet, so X-User-Roles must be set
by hand when testing these directly.
"""

import uuid

from account.deps import get_admin_editor_service
from account.schemas.admin import CreateEditorRequest, UpdateEditorRequest, UpdateStatusRequest
from account.schemas.user import UserProfileResponse
from account.services.admin_editor_service import AdminEditorService
from fastapi import APIRouter, Depends, Query, status
from pbl6_common.deps import UserContext, require_role
from pbl6_common.pagination import Paginated

router = APIRouter(prefix="/admin/editors", tags=["admin"])

_require_admin = require_role("ADMIN")


@router.post("", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_editor(
    body: CreateEditorRequest,
    _: UserContext = Depends(_require_admin),
    svc: AdminEditorService = Depends(get_admin_editor_service),
):
    return await svc.create_editor(
        email=body.email, password=body.password, full_name=body.full_name
    )


@router.get("", response_model=Paginated[UserProfileResponse])
async def list_editors(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    _: UserContext = Depends(_require_admin),
    svc: AdminEditorService = Depends(get_admin_editor_service),
):
    items, total = await svc.list_editors(page=page, size=size)
    return Paginated(items=list(items), total=total, page=page, size=size)


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_editor(
    user_id: uuid.UUID,
    _: UserContext = Depends(_require_admin),
    svc: AdminEditorService = Depends(get_admin_editor_service),
):
    return await svc.get_editor(user_id)


@router.patch("/{user_id}", response_model=UserProfileResponse)
async def update_editor(
    user_id: uuid.UUID,
    body: UpdateEditorRequest,
    _: UserContext = Depends(_require_admin),
    svc: AdminEditorService = Depends(get_admin_editor_service),
):
    return await svc.update_editor(user_id, full_name=body.full_name)


@router.patch("/{user_id}/status", response_model=UserProfileResponse)
async def update_editor_status(
    user_id: uuid.UUID,
    body: UpdateStatusRequest,
    _: UserContext = Depends(_require_admin),
    svc: AdminEditorService = Depends(get_admin_editor_service),
):
    return await svc.set_status(user_id, status=body.status)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_editor(
    user_id: uuid.UUID,
    _: UserContext = Depends(_require_admin),
    svc: AdminEditorService = Depends(get_admin_editor_service),
):
    await svc.delete_editor(user_id)
