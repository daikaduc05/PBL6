import uuid

from content.models.lesson import Lesson, LessonStatus
from content.repositories.category_repository import CategoryRepository
from content.repositories.lesson_repository import LessonRepository
from content.schemas.lesson import LessonCreate, LessonUpdate
from fastapi import HTTPException
from pbl6_common.events.publisher import EventPublisher


class LessonService:
    def __init__(
        self,
        lesson_repo: LessonRepository,
        category_repo: CategoryRepository,
        publisher: EventPublisher,
    ):
        self._lesson_repo = lesson_repo
        self._category_repo = category_repo
        self._publisher = publisher

    async def get_lesson(self, lesson_id: uuid.UUID) -> Lesson | None:
        return await self._lesson_repo.get_by_id(lesson_id)

    async def get_lessons(
        self,
        category_id: uuid.UUID | None = None,
        level: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Lesson]:
        return await self._lesson_repo.get_all(
            category_id=category_id, level=level, limit=limit, offset=offset
        )

    async def create_lesson(self, data: LessonCreate) -> Lesson:
        category = await self._category_repo.get_by_id(data.category_id)
        if not category:
            raise HTTPException(status_code=400, detail="Danh mục không tồn tại.")

        return await self._lesson_repo.create(
            category_id=data.category_id,
            title=data.title,
            body=data.body,
            level=data.level,
            access=data.access,
            status=LessonStatus.DRAFT,
        )

    async def update_lesson(self, lesson_id: uuid.UUID, data: LessonUpdate) -> Lesson:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài học.")

        if lesson.status != LessonStatus.DRAFT:
            raise HTTPException(
                status_code=400, detail="Chỉ có thể sửa bài học khi đang ở trạng thái DRAFT."
            )

        if data.category_id and data.category_id != lesson.category_id:
            category = await self._category_repo.get_by_id(data.category_id)
            if not category:
                raise HTTPException(status_code=400, detail="Danh mục không tồn tại.")

        update_data = data.model_dump(exclude_unset=True)
        return await self._lesson_repo.update(lesson, update_data)

    async def delete_lesson(self, lesson_id: uuid.UUID) -> None:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài học.")

        await self._lesson_repo.delete(lesson)

    async def submit_lesson(self, lesson_id: uuid.UUID) -> Lesson:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài học.")

        if lesson.status != LessonStatus.DRAFT:
            raise HTTPException(
                status_code=400, detail="Chỉ có thể submit bài học khi đang ở trạng thái DRAFT."
            )

        return await self._lesson_repo.update(lesson, {"status": LessonStatus.PENDING})

    async def approve_lesson(self, lesson_id: uuid.UUID) -> Lesson:
        lesson = await self._lesson_repo.get_by_id(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Không tìm thấy bài học.")

        if lesson.status != LessonStatus.PENDING:
            raise HTTPException(
                status_code=400, detail="Chỉ có thể duyệt bài học khi đang ở trạng thái PENDING."
            )

        updated = await self._lesson_repo.update(lesson, {"status": LessonStatus.PUBLISHED})

        await self._publisher.publish(
            "lesson.published",
            {
                "lesson_id": str(updated.id),
                "title": updated.title,
                "category_id": str(updated.category_id),
            },
        )

        return updated
