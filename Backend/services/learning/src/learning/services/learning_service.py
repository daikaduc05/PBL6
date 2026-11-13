from datetime import UTC, datetime
from uuid import UUID

from learning.repositories.history_repository import HistoryRepository
from learning.schemas.activity import (
    HistoryResponse,
    LastActivityResponse,
    UserActivityItem,
    UserLastActivityResponse,
)


class LearningService:
    def __init__(self, history_repo: HistoryRepository):
        self.history_repo = history_repo

    async def get_user_history(self, user_id: UUID) -> list[HistoryResponse]:
        histories = await self.history_repo.list_by_user(user_id)
        return [HistoryResponse.model_validate(h) for h in histories]

    async def get_last_activity_for_user(self, user_id: UUID) -> UserLastActivityResponse:
        last = await self.history_repo.get_last_activity_for_user(user_id)
        if not last:
            return UserLastActivityResponse(
                user_id=user_id,
                has_studied_today=False,
            )

        now = datetime.now(UTC)
        has_studied_today = last.completed_at.date() == now.date()

        return UserLastActivityResponse(
            user_id=user_id,
            last_activity_at=last.completed_at,
            lesson_id=last.lesson_id,
            highest_score=last.highest_score,
            has_studied_today=has_studied_today,
        )

    async def get_last_activities(
        self, since: datetime | None = None, limit: int = 1000
    ) -> LastActivityResponse:
        histories = await self.history_repo.get_last_activities(since=since, limit=limit)
        items = [
            UserActivityItem(
                user_id=h.user_id,
                lesson_id=h.lesson_id,
                highest_score=h.highest_score,
                last_activity_at=h.completed_at,
            )
            for h in histories
        ]
        return LastActivityResponse(items=items, total=len(items))
