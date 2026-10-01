"""T23 — HTTP layer only, no business logic (backend.md §3 layering rule).

    GET    /api/v1/admin/users                 admin  — list students, paginated
    GET    /api/v1/admin/users/{id}             admin  — one student
    PATCH  /api/v1/admin/users/{id}             admin  — edit full_name
    PATCH  /api/v1/admin/users/{id}/status      admin  — ACTIVE / INACTIVE / LOCKED
    PATCH  /api/v1/admin/users/{id}/vip         admin  — grant/revoke VIP manually
    DELETE /api/v1/admin/users/{id}             admin  — soft delete

"admin" means the gateway forwarded X-User-Roles containing ADMIN
(pbl6_common.require_role) — same interim gap as T22 until the gateway
(T08/T09) exists: set the header by hand when testing directly.
"""

import uuid

from account.deps import get_admin_user_service
from account.schemas.admin import (
    UpdateStatusRequest,
    UpdateStudentRequest,
    UpdateStudentVipRequest,
)
from account.schemas.user import UserProfileResponse
from account.services.admin_user_service import AdminUserService
from fastapi import APIRouter, Depends, Query, status
from pbl6_common.deps import UserContext, require_role
from pbl6_common.pagination import Paginated

router = APIRouter(prefix="/admin/users", tags=["admin"])

_require_admin = require_role("ADMIN")


@router.get("", response_model=Paginated[UserProfileResponse])
async def list_students(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    _: UserContext = Depends(_require_admin),
    svc: AdminUserService = Depends(get_admin_user_service),
):
    items, total = await svc.list_students(page=page, size=size)
    return Paginated(items=list(items), total=total, page=page, size=size)


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_student(
    user_id: uuid.UUID,
    _: UserContext = Depends(_require_admin),
    svc: AdminUserService = Depends(get_admin_user_service),
):
    return await svc.get_student(user_id)


@router.patch("/{user_id}", response_model=UserProfileResponse)
async def update_student(
    user_id: uuid.UUID,
    body: UpdateStudentRequest,
    _: UserContext = Depends(_require_admin),
    svc: AdminUserService = Depends(get_admin_user_service),
):
    return await svc.update_student(user_id, full_name=body.full_name)


@router.patch("/{user_id}/status", response_model=UserProfileResponse)
async def update_student_status(
    user_id: uuid.UUID,
    body: UpdateStatusRequest,
    _: UserContext = Depends(_require_admin),
    svc: AdminUserService = Depends(get_admin_user_service),
):
    return await svc.set_status(user_id, status=body.status)


@router.patch("/{user_id}/vip", response_model=UserProfileResponse)
async def update_student_vip(
    user_id: uuid.UUID,
    body: UpdateStudentVipRequest,
    _: UserContext = Depends(_require_admin),
    svc: AdminUserService = Depends(get_admin_user_service),
):
    return await svc.set_vip(user_id, is_vip=body.is_vip, vip_expired_at=body.vip_expired_at)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    user_id: uuid.UUID,
    _: UserContext = Depends(_require_admin),
    svc: AdminUserService = Depends(get_admin_user_service),
):
    await svc.delete_student(user_id)
