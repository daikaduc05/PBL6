"""Service-local dependency wiring: this service's own DB engine/session."""

from __future__ import annotations

from fastapi import Depends
from pbl6_common.db import make_engine, make_get_db, make_session_factory
from sqlalchemy.ext.asyncio import AsyncSession

from content.config import get_settings
from content.repositories.category_repository import CategoryRepository
from content.repositories.lesson_repository import LessonRepository
from content.repositories.media_repository import MediaRepository
from content.repositories.outbox_repository import OutboxRepository
from content.services.category_service import CategoryService
from content.services.lesson_service import LessonService
from content.services.media_service import MediaService

settings = get_settings()
engine = make_engine(settings.database_url)
session_factory = make_session_factory(engine)
_session_factory = session_factory
get_db = make_get_db(_session_factory)


async def get_category_repo(db: AsyncSession = Depends(get_db)) -> CategoryRepository:
    return CategoryRepository(db)


async def get_category_service(
    repo: CategoryRepository = Depends(get_category_repo),
) -> CategoryService:
    return CategoryService(repo)


async def get_lesson_repo(db: AsyncSession = Depends(get_db)) -> LessonRepository:
    return LessonRepository(db)


async def get_outbox_repo(db: AsyncSession = Depends(get_db)) -> OutboxRepository:
    return OutboxRepository(db)


async def get_lesson_service(
    lesson_repo: LessonRepository = Depends(get_lesson_repo),
    category_repo: CategoryRepository = Depends(get_category_repo),
    outbox_repo: OutboxRepository = Depends(get_outbox_repo),
) -> LessonService:
    return LessonService(lesson_repo, category_repo, outbox_repo=outbox_repo)


async def get_media_repo(db: AsyncSession = Depends(get_db)) -> MediaRepository:
    return MediaRepository(db)


async def get_media_service(
    media_repo: MediaRepository = Depends(get_media_repo),
    lesson_repo: LessonRepository = Depends(get_lesson_repo),
) -> MediaService:
    return MediaService(media_repo, lesson_repo)
