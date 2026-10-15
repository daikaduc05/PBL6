"""Unit tests: repository is a fake — no database, no network."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from account.models.user import User
from account.services.admin_user_service import AdminUserService
from pbl6_common.errors import NotFoundError


class FakeUserRepository:
    def __init__(self):
        self._by_id: dict[uuid.UUID, User] = {}

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._by_id.get(user_id)

    async def save(self, user: User) -> None:
        self._by_id[user.id] = user

    async def list_by_role(
        self,
        *,
        role: str,
        page: int,
        size: int,
        status: str | None = None,
        q: str | None = None,
    ) -> tuple[list[User], int]:
        matches = [u for u in self._by_id.values() if u.role == role and not u.deleted_at]
        if status is not None:
            matches = [u for u in matches if u.status == status]
        if q:
            needle = q.lower()
            matches = [
                u for u in matches if needle in u.full_name.lower() or needle in u.email.lower()
            ]
        matches.sort(key=lambda u: u.created_at, reverse=True)
        start = (page - 1) * size
        return matches[start : start + size], len(matches)

    def seed(self, **kwargs) -> User:
        user = User(
            id=uuid.uuid4(),
            email=kwargs.pop("email", f"{uuid.uuid4()}@vidu.com"),
            password_hash="x",
            full_name=kwargs.pop("full_name", "A B"),
            role=kwargs.pop("role", "CUSTOMER"),
            status=kwargs.pop("status", "ACTIVE"),
            is_vip=kwargs.pop("is_vip", False),
            created_at=kwargs.pop("created_at", datetime.now(UTC)),
        )
        self._by_id[user.id] = user
        return user


class FakeEventPublisher:
    def __init__(self) -> None:
        self.published: list[tuple[str, dict]] = []

    async def publish(self, event_type: str, data: dict) -> None:
        self.published.append((event_type, data))


def make_service() -> tuple[AdminUserService, FakeUserRepository, FakeEventPublisher]:
    users = FakeUserRepository()
    publisher = FakeEventPublisher()
    return AdminUserService(users=users, publisher=publisher), users, publisher


@pytest.mark.asyncio
async def test_list_students_excludes_editors_and_deleted():
    service, users, _publisher = make_service()
    users.seed(role="CUSTOMER")
    users.seed(role="EDITOR")
    deleted = users.seed(role="CUSTOMER")
    deleted.deleted_at = datetime.now(UTC)

    items, total = await service.list_students(page=1, size=20)
    assert total == 1
    assert all(u.role == "CUSTOMER" for u in items)


@pytest.mark.asyncio
async def test_get_student_404_for_editor():
    service, users, _publisher = make_service()
    editor = users.seed(role="EDITOR")
    with pytest.raises(NotFoundError):
        await service.get_student(editor.id)


@pytest.mark.asyncio
async def test_get_student_404_for_unknown_id():
    service, _, _ = make_service()
    with pytest.raises(NotFoundError):
        await service.get_student(uuid.uuid4())


@pytest.mark.asyncio
async def test_update_student_changes_full_name():
    service, users, _publisher = make_service()
    student = users.seed(full_name="Old")
    updated = await service.update_student(student.id, full_name="New")
    assert updated.full_name == "New"


@pytest.mark.asyncio
async def test_set_status_locks_account():
    service, users, _publisher = make_service()
    student = users.seed(status="ACTIVE")
    updated = await service.set_status(student.id, status="LOCKED")
    assert updated.status == "LOCKED"


@pytest.mark.asyncio
async def test_set_status_to_locked_publishes_account_locked():
    service, users, publisher = make_service()
    student = users.seed(status="ACTIVE")
    admin_id = uuid.uuid4()

    await service.set_status(student.id, status="LOCKED", locked_by=admin_id, reason="spam reports")

    assert publisher.published == [
        (
            "account.locked",
            {"user_id": str(student.id), "locked_by": str(admin_id), "reason": "spam reports"},
        )
    ]


@pytest.mark.asyncio
async def test_set_status_away_from_locked_publishes_account_unlocked():
    service, users, publisher = make_service()
    student = users.seed(status="LOCKED")

    await service.set_status(student.id, status="ACTIVE")

    assert publisher.published == [("account.unlocked", {"user_id": str(student.id)})]


@pytest.mark.asyncio
async def test_set_status_plain_active_inactive_toggle_publishes_nothing():
    """ACTIVE<->INACTIVE never touches the LOCKED boundary — not in the
    event contract (backend.md §6 only defines account.locked/unlocked)."""
    service, users, publisher = make_service()
    student = users.seed(status="ACTIVE")

    await service.set_status(student.id, status="INACTIVE")

    assert publisher.published == []


@pytest.mark.asyncio
async def test_set_status_relocking_an_already_locked_account_is_a_noop():
    service, users, publisher = make_service()
    student = users.seed(status="LOCKED")

    await service.set_status(student.id, status="LOCKED")

    assert publisher.published == []


@pytest.mark.asyncio
async def test_set_vip_grants_and_clears_expiry_on_revoke():
    service, users, _publisher = make_service()
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
    service, users, _publisher = make_service()
    users.seed(full_name="Active One", status="ACTIVE")
    users.seed(full_name="Locked One", status="LOCKED")

    items, total = await service.list_students(page=1, size=20, status="LOCKED")
    assert total == 1
    assert items[0].full_name == "Locked One"


@pytest.mark.asyncio
async def test_list_students_search_matches_name_or_email():
    service, users, _publisher = make_service()
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
    service, users, _publisher = make_service()
    student = users.seed()
    await service.delete_student(student.id)
    with pytest.raises(NotFoundError):
        await service.get_student(student.id)
