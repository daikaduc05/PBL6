import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pbl6_common.deps import require_role
from pydantic import BaseModel

from content.deps import get_lesson_service
from content.schemas.lesson import (
    LessonCreate,
    LessonResponse,
    LessonUpdate,
)
from content.services.lesson_service import LessonService

router = APIRouter(prefix="/lessons", tags=["Lessons"])


class LessonListResponse(BaseModel):
    items: list[LessonResponse]
    total: int
    page: int
    size: int


@router.get("", response_model=LessonListResponse)
async def list_lessons(
    category_id: uuid.UUID | None = None,
    level: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    service: LessonService = Depends(get_lesson_service),
):
    offset = (page - 1) * size
    lessons = await service.get_lessons(
        category_id=category_id, level=level, limit=size, offset=offset
    )
    # TODO: Tích hợp query đếm tổng số lượng (total) nếu cần, tạm thời để total = len(items)
    return {
        "items": lessons,
        "total": len(lessons),
        "page": page,
        "size": size,
    }


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: uuid.UUID,
    service: LessonService = Depends(get_lesson_service),
):
    # TODO: Ở sprint 2 sẽ xử lý cắt teaser đối với public user nếu bài học VIP
    lesson = await service.get_lesson(lesson_id)
    if not lesson:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Không tìm thấy bài học.")
    return lesson


@router.post(
    "",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "editor"))],
)
async def create_lesson(
    data: LessonCreate,
    service: LessonService = Depends(get_lesson_service),
):
    return await service.create_lesson(data)


@router.put(
    "/{lesson_id}",
    response_model=LessonResponse,
    dependencies=[Depends(require_role("admin", "editor"))],
)
async def update_lesson(
    lesson_id: uuid.UUID,
    data: LessonUpdate,
    service: LessonService = Depends(get_lesson_service),
):
    return await service.update_lesson(lesson_id, data)


@router.delete(
    "/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin", "editor"))],
)
async def delete_lesson(
    lesson_id: uuid.UUID,
    service: LessonService = Depends(get_lesson_service),
):
    await service.delete_lesson(lesson_id)


@router.post(
    "/{lesson_id}/submit",
    response_model=LessonResponse,
    dependencies=[Depends(require_role("admin", "editor"))],
)
async def submit_lesson(
    lesson_id: uuid.UUID,
    service: LessonService = Depends(get_lesson_service),
):
    return await service.submit_lesson(lesson_id)


@router.post(
    "/{lesson_id}/approve",
    response_model=LessonResponse,
    dependencies=[Depends(require_role("admin"))],
)
async def approve_lesson(
    lesson_id: uuid.UUID,
    service: LessonService = Depends(get_lesson_service),
):
    return await service.approve_lesson(lesson_id)
