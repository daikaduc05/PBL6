"""Unit tests: repository is a fake — no database, no network."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from account.services.admin_editor_service import AdminEditorService
from fakes import FakeUserRepository
from pbl6_common.errors import ConflictError, NotFoundError
from pbl6_common.security import verify_password


def make_service() -> tuple[AdminEditorService, FakeUserRepository]:
    users = FakeUserRepository()
    return AdminEditorService(users=users), users


@pytest.mark.asyncio
async def test_create_editor_sets_role_and_hashes_password():
    service, users = make_service()
    editor = await service.create_editor(
        email="editor@vidu.com", password="password123", full_name="Editor One"
    )
    assert editor.role == "EDITOR"
    assert editor.password_hash != "password123"
    assert verify_password("password123", editor.password_hash)


@pytest.mark.asyncio
async def test_create_editor_rejects_duplicate_email():
    service, users = make_service()
    users.seed(email="dup@vidu.com", role="CUSTOMER")
    with pytest.raises(ConflictError):
        await service.create_editor(email="Dup@vidu.com", password="password123", full_name="X")


@pytest.mark.asyncio
async def test_list_editors_excludes_customers_and_deleted():
    service, users = make_service()
    users.seed(role="EDITOR")
    users.seed(role="CUSTOMER")
    deleted = users.seed(role="EDITOR")
    deleted.deleted_at = datetime.now(UTC)

    items, total = await service.list_editors(page=1, size=20)
    assert total == 1
    assert all(u.role == "EDITOR" for u in items)


@pytest.mark.asyncio
async def test_get_editor_404_for_customer():
    service, users = make_service()
    student = users.seed(role="CUSTOMER")
    with pytest.raises(NotFoundError):
        await service.get_editor(student.id)


@pytest.mark.asyncio
async def test_update_editor_changes_full_name():
    service, users = make_service()
    editor = users.seed(role="EDITOR", full_name="Old")
    updated = await service.update_editor(editor.id, full_name="New")
    assert updated.full_name == "New"


@pytest.mark.asyncio
async def test_set_status_locks_editor():
    service, users = make_service()
    editor = users.seed(role="EDITOR", status="ACTIVE")
    updated = await service.set_status(editor.id, status="LOCKED")
    assert updated.status == "LOCKED"


@pytest.mark.asyncio
async def test_list_editors_filters_by_status():
    service, users = make_service()
    users.seed(role="EDITOR", full_name="Active Editor", status="ACTIVE")
    users.seed(role="EDITOR", full_name="Locked Editor", status="LOCKED")

    items, total = await service.list_editors(page=1, size=20, status="LOCKED")
    assert total == 1
    assert items[0].full_name == "Locked Editor"


@pytest.mark.asyncio
async def test_list_editors_search_matches_name_or_email():
    service, users = make_service()
    users.seed(role="EDITOR", full_name="Nguyen Van A", email="a@vidu.com")
    users.seed(role="EDITOR", full_name="Tran Thi B", email="b@vidu.com")

    items, total = await service.list_editors(page=1, size=20, q="tran")
    assert total == 1
    assert items[0].full_name == "Tran Thi B"


@pytest.mark.asyncio
async def test_delete_editor_soft_deletes():
    service, users = make_service()
    editor = users.seed(role="EDITOR")
    await service.delete_editor(editor.id)
    with pytest.raises(NotFoundError):
        await service.get_editor(editor.id)
