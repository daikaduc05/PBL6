"""Service-local dependency wiring: this service's own DB engine/session.
Auth dependencies are provided by `pbl6_common.deps`."""

from __future__ import annotations

from fastapi import Depends
from learning.config import get_settings
from learning.repositories.history_repository import HistoryRepository
from learning.repositories.quiz_repository import QuizRepository
from learning.services.learning_service import LearningService
from learning.services.quiz_service import QuizService
from pbl6_common.db import make_engine, make_get_db, make_session_factory
from sqlalchemy.ext.asyncio import AsyncSession

settings = get_settings()
engine = make_engine(settings.database_url)
_session_factory = make_session_factory(engine)
get_db = make_get_db(_session_factory)


async def get_quiz_repo(db: AsyncSession = Depends(get_db)) -> QuizRepository:
    return QuizRepository(db)


async def get_history_repo(db: AsyncSession = Depends(get_db)) -> HistoryRepository:
    return HistoryRepository(db)


async def get_quiz_service(
    quiz_repo: QuizRepository = Depends(get_quiz_repo),
    history_repo: HistoryRepository = Depends(get_history_repo),
) -> QuizService:
    return QuizService(quiz_repo, history_repo)


async def get_learning_service(
    history_repo: HistoryRepository = Depends(get_history_repo),
) -> LearningService:
    return LearningService(history_repo)
