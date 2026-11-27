"""Unit tests for Content Service (Categories, Lessons, Outbox, and RBAC)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import cast

import pytest
from content.models.category import Category
from content.models.lesson import Lesson, LessonAccess, LessonLevel, LessonStatus
from content.models.outbox import OutboxEntry
from content.schemas.category import CategoryCreate
from content.schemas.lesson import LessonCreate
from content.services.category_service import CategoryService
from content.services.lesson_service import LessonService
from pbl6_common.errors import AppError, ConflictError


class FakeCategoryRepository:
    def __init__(self) -> None:
        self._items: dict[uuid.UUID, Category] = {}
        self.lessons_in_category: set[uuid.UUID] = set()

    async def get_by_id(self, category_id: uuid.UUID) -> Category | None:
        return self._items.get(category_id)

    async def get_by_slug(self, slug: str) -> Category | None:
        return next((c for c in self._items.values() if c.slug == slug), None)

    async def get_all(self, q: str | None = None) -> list[Category]:
        return list(self._items.values())

    async def create(
        self, name: str, slug: str, parent_id: uuid.UUID | None, sort_order: int
    ) -> Category:
        cat_id = uuid.uuid4()
        cat = Category(
            id=cat_id,
            name=name,
            slug=slug,
            parent_id=parent_id,
            sort_order=sort_order,
        )
        self._items[cat_id] = cat
        return cat

    async def update(self, category: Category, update_data: dict) -> Category:
        for k, v in update_data.items():
            setattr(category, k, v)
        return category

    async def delete(self, category: Category) -> None:
        self._items.pop(cast(uuid.UUID, category.id), None)

    async def get_children(self, parent_id: uuid.UUID) -> list[Category]:
        return [c for c in self._items.values() if c.parent_id == parent_id]

    async def has_lessons(self, category_id: uuid.UUID) -> bool:
        return category_id in self.lessons_in_category


class FakeLessonRepository:
    def __init__(self) -> None:
        self._items: dict[uuid.UUID, Lesson] = {}

    async def get_by_id(self, lesson_id: uuid.UUID) -> Lesson | None:
        return self._items.get(lesson_id)

    async def get_all(
        self,
        category_id: uuid.UUID | None = None,
        level: str | None = None,
        q: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Lesson]:
        return list(self._items.values())

    async def create(
        self,
        category_id: uuid.UUID,
        title: str,
        body: str,
        level: LessonLevel,
        access: LessonAccess,
        status: LessonStatus = LessonStatus.DRAFT,
    ) -> Lesson:
        now = datetime.now(UTC)
        lesson_id = uuid.uuid4()
        lesson = Lesson(
            id=lesson_id,
            category_id=category_id,
            title=title,
            body=body,
            level=level,
            access=access,
            status=status,
            created_at=now,
            updated_at=now,
        )
        self._items[lesson_id] = lesson
        return lesson

    async def update(self, lesson: Lesson, update_data: dict) -> Lesson:
        for k, v in update_data.items():
            setattr(lesson, k, v)
        return lesson

    async def delete(self, lesson: Lesson) -> None:
        self._items.pop(cast(uuid.UUID, lesson.id), None)


class FakeOutboxRepository:
    def __init__(self) -> None:
        self.entries: list[OutboxEntry] = []

    async def create(
        self, *, aggregate_id: uuid.UUID, event_type: str, payload: dict
    ) -> OutboxEntry:
        entry = OutboxEntry(
            id=uuid.uuid4(),
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=payload,
            created_at=datetime.now(UTC),
        )
        self.entries.append(entry)
        return entry


@pytest.mark.asyncio
async def test_category_duplicate_slug_raises_conflict_app_error():
    repo = FakeCategoryRepository()
    svc = CategoryService(repo)

    await svc.create_category(CategoryCreate(name="Ngữ pháp", slug="ngu-phap", sort_order=1))

    with pytest.raises(ConflictError) as exc_info:
        await svc.create_category(CategoryCreate(name="Ngữ pháp 2", slug="ngu-phap", sort_order=2))
    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "CONFLICT"


@pytest.mark.asyncio
async def test_delete_category_with_linked_lessons_raises_app_error():
    repo = FakeCategoryRepository()
    svc = CategoryService(repo)
    cat = await svc.create_category(CategoryCreate(name="Từ vựng", slug="tu-vung", sort_order=1))
    repo.lessons_in_category.add(cast(uuid.UUID, cat.id))

    with pytest.raises(AppError) as exc_info:
        await svc.delete_category(cast(uuid.UUID, cat.id))
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_approve_lesson_writes_lesson_published_to_outbox():
    cat_repo = FakeCategoryRepository()
    lesson_repo = FakeLessonRepository()
    outbox_repo = FakeOutboxRepository()
    cat = await cat_repo.create("IELTS", "ielts", None, 1)

    svc = LessonService(lesson_repo, cat_repo, outbox_repo=outbox_repo)  # type: ignore[arg-type]
    lesson = await svc.create_lesson(
        LessonCreate(
            title="IELTS Reading Tips",
            body="Nội dung bài học",
            category_id=cast(uuid.UUID, cat.id),
            level=LessonLevel.MEDIUM,
            access=LessonAccess.PUBLIC,
        )
    )
    assert lesson.status == LessonStatus.DRAFT

    await svc.submit_lesson(cast(uuid.UUID, lesson.id))
    approved = await svc.approve_lesson(cast(uuid.UUID, lesson.id))

    assert approved.status == LessonStatus.PUBLISHED
    assert len(outbox_repo.entries) == 1
    assert outbox_repo.entries[0].event_type == "lesson.published"
    assert outbox_repo.entries[0].payload["lesson_id"] == str(lesson.id)
    assert outbox_repo.entries[0].payload["title"] == "IELTS Reading Tips"
