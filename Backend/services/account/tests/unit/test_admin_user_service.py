"""Unit tests: repository is a fake — no database, no network."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from account.services.admin_user_service import AdminUserService
from fakes import FakeUserRepository
from pbl6_common.errors import NotFoundError


def make_service() -> tuple[AdminUserService, FakeUserRepository]:
    users = FakeUserRepository()
    return AdminUserService(users=users), users


@pytest.mark.asyncio
async def test_list_students_excludes_editors_and_deleted():
    service, users = make_service()
    users.seed(role="CUSTOMER")
    users.seed(role="EDITOR")
    deleted = users.seed(role="CUSTOMER")
    deleted.deleted_at = datetime.now(UTC)

    items, total = await service.list_students(page=1, size=20)
    assert total == 1
    assert all(u.role == "CUSTOMER" for u in items)


@pytest.mark.asyncio
async def test_get_student_404_for_editor():
    service, users = make_service()
    editor = users.seed(role="EDITOR")
    with pytest.raises(NotFoundError):
        await service.get_student(editor.id)


@pytest.mark.asyncio
async def test_get_student_404_for_unknown_id():
    service, _ = make_service()
    with pytest.raises(NotFoundError):
        await service.get_student(uuid.uuid4())


@pytest.mark.asyncio
async def test_update_student_changes_full_name():
    service, users = make_service()
    student = users.seed(full_name="Old")
    updated = await service.update_student(student.id, full_name="New")
    assert updated.full_name == "New"


@pytest.mark.asyncio
async def test_set_status_locks_account():
    service, users = make_service()
    student = users.seed(status="ACTIVE")
    updated = await service.set_status(student.id, status="LOCKED")
    assert updated.status == "LOCKED"


@pytest.mark.asyncio
async def test_set_vip_grants_and_clears_expiry_on_revoke():
    service, users = make_service()
    student = users.seed(is_vip=False)

    expiry = datetime.now(UTC) + timedelta(days=30)
    granted = await service.set_vip(student.id, is_vip=True, vip_expired_at=expiry)
    assert granted.is_vip is True
    assert granted.vip_expired_at == expiry

    revoked = await service.set_vip(student.id, is_vip=False, vip_expired_at=expiry)
    assert revoked.is_vip is False
    assert revoked.vip_expired_at is None


@pytest.mark.asyncio
async def test_list_students_filters_by_status():
    service, users = make_service()
    users.seed(full_name="Active One", status="ACTIVE")
    users.seed(full_name="Locked One", status="LOCKED")

    items, total = await service.list_students(page=1, size=20, status="LOCKED")
    assert total == 1
    assert items[0].full_name == "Locked One"


@pytest.mark.asyncio
async def test_list_students_search_matches_name_or_email():
    service, users = make_service()
    users.seed(full_name="Nguyen Van A", email="a@vidu.com")
    users.seed(full_name="Tran Thi B", email="b@vidu.com")

    by_name, total1 = await service.list_students(page=1, size=20, q="nguyen")
    assert total1 == 1
    assert by_name[0].full_name == "Nguyen Van A"

    by_email, total2 = await service.list_students(page=1, size=20, q="b@vidu")
    assert total2 == 1
    assert by_email[0].email == "b@vidu.com"


@pytest.mark.asyncio
async def test_delete_student_soft_deletes():
    service, users = make_service()
    student = users.seed()
    await service.delete_student(student.id)
    with pytest.raises(NotFoundError):
        await service.get_student(student.id)
