"""Service-local dependency wiring: this service's own DB engine/session."""

from __future__ import annotations

from fastapi import Depends
from pbl6_common.db import make_engine, make_get_db, make_session_factory
from pbl6_common.events.publisher import EventPublisher
from sqlalchemy.ext.asyncio import AsyncSession

from content.config import get_settings
from content.repositories.category_repository import CategoryRepository
from content.repositories.lesson_repository import LessonRepository
from content.services.category_service import CategoryService
from content.services.lesson_service import LessonService

settings = get_settings()
engine = make_engine(settings.database_url)
_session_factory = make_session_factory(engine)
get_db = make_get_db(_session_factory)
_publisher = EventPublisher(settings.rabbitmq_url, "pbl6.events", "content-service")


async def get_category_repo(db: AsyncSession = Depends(get_db)) -> CategoryRepository:
    return CategoryRepository(db)


async def get_category_service(
    repo: CategoryRepository = Depends(get_category_repo),
) -> CategoryService:
    return CategoryService(repo)


async def get_lesson_repo(db: AsyncSession = Depends(get_db)) -> LessonRepository:
    return LessonRepository(db)


async def get_lesson_service(
    lesson_repo: LessonRepository = Depends(get_lesson_repo),
    category_repo: CategoryRepository = Depends(get_category_repo),
) -> LessonService:
    return LessonService(lesson_repo, category_repo, _publisher)
