"""Function 8.1 — the daily study reminder.

Each learner picks the hour they want to be nudged at, so the scheduler wakes
once an hour and this service answers one question: *who asked for the hour
that just started, has not studied yet today, and has not already been
reminded?*

Everything is expressed in Asia/Ho_Chi_Minh. "Today" means the learner's day,
not the server's — a container running on UTC would otherwise reset the
"already studied" window at 07:00 local time.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from notification.models.setting import DEFAULT_REMINDER_HOUR
from notification.repositories.external_reader import ActiveUser

logger = logging.getLogger(__name__)


# Depending on protocols rather than the concrete repositories keeps the
# selection rules testable without a database, and documents exactly how
# little of each collaborator this feature actually uses.


class MessageWriter(Protocol):
    async def create(self, *, user_id: uuid.UUID, title: str, content: str) -> Any: ...

    async def user_ids_with_title_since(self, *, title: str, since: datetime) -> set[uuid.UUID]: ...


class ReminderPreferences(Protocol):
    async def user_ids_wanting_hour(self, hour: int) -> set[uuid.UUID]: ...

    async def user_ids_with_a_row(self) -> set[uuid.UUID]: ...


class LearnerSource(Protocol):
    async def active_users(self) -> list[ActiveUser]: ...

    async def user_ids_studied_since(self, since: datetime) -> set[uuid.UUID]: ...


class Mailer(Protocol):
    async def send(self, *, to: str, template: str, context: dict[str, Any]) -> bool: ...


STUDY_REMINDER_TITLE = "Đã đến giờ học hôm nay"
STUDY_REMINDER_BODY = (
    "Hôm nay bạn chưa hoàn thành bài học nào. Dành ra mười phút để giữ nhịp học nhé."
)


@dataclass(frozen=True)
class ReminderRun:
    """What one pass did — returned so tests and logs can see inside."""

    hour: int
    candidates: int = 0
    skipped_already_studied: int = 0
    skipped_already_reminded: int = 0
    notified: int = 0
    emails_sent: int = 0


class ReminderService:
    def __init__(
        self,
        *,
        messages: MessageWriter,
        settings: ReminderPreferences,
        external: LearnerSource,
        email: Mailer,
        email_batch_size: int = 50,
        email_batch_pause_seconds: float = 1.0,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._messages = messages
        self._settings = settings
        self._external = external
        self._email = email
        self._email_batch_size = email_batch_size
        self._email_batch_pause_seconds = email_batch_pause_seconds
        self._sleep = sleep

    async def pick_recipients(
        self, *, hour: int, day_start: datetime
    ) -> tuple[list[ActiveUser], ReminderRun]:
        """Decide who gets reminded, without sending anything.

        Split out from ``run`` so the selection rules can be tested on their
        own — they are where the interesting edge cases live.
        """
        explicit = await self._settings.user_ids_wanting_hour(hour)
        configured = await self._settings.user_ids_with_a_row()
        users = await self._external.active_users()

        # Two ways to qualify. The second one matters: most learners never open
        # the settings screen, so they have no row at all and must still be
        # reminded — at the default hour.
        candidates = [
            user
            for user in users
            if user.id in explicit or (user.id not in configured and hour == DEFAULT_REMINDER_HOUR)
        ]
        run = ReminderRun(hour=hour, candidates=len(candidates))

        if not candidates:
            return [], run

        studied = await self._external.user_ids_studied_since(day_start)
        after_studied = [u for u in candidates if u.id not in studied]

        reminded = await self._messages.user_ids_with_title_since(
            title=STUDY_REMINDER_TITLE, since=day_start
        )
        recipients = [u for u in after_studied if u.id not in reminded]

        run = ReminderRun(
            hour=hour,
            candidates=len(candidates),
            skipped_already_studied=len(candidates) - len(after_studied),
            skipped_already_reminded=len(after_studied) - len(recipients),
        )
        return recipients, run

    async def run(self, *, hour: int, day_start: datetime) -> ReminderRun:
        """Create the in-app notifications, then send the emails.

        Order is deliberate. The caller commits the notifications before any
        email goes out, so a crash halfway through the mailing leaves the
        in-app record correct and the next run skips those users rather than
        notifying them twice. Losing an email is recoverable; a duplicate
        notification is what users actually notice.
        """
        recipients, run = await self.pick_recipients(hour=hour, day_start=day_start)
        if not recipients:
            logger.info("reminder hour=%s: nobody to notify (%s)", hour, run)
            return run

        for user in recipients:
            await self._messages.create(
                user_id=user.id,
                title=STUDY_REMINDER_TITLE,
                content=STUDY_REMINDER_BODY,
            )

        sent = await self._send_emails(recipients)

        result = ReminderRun(
            hour=run.hour,
            candidates=run.candidates,
            skipped_already_studied=run.skipped_already_studied,
            skipped_already_reminded=run.skipped_already_reminded,
            notified=len(recipients),
            emails_sent=sent,
        )
        logger.info("reminder hour=%s: %s", hour, result)
        return result

    async def _send_emails(self, recipients: list[ActiveUser]) -> int:
        """Send in batches with a short pause.

        Gmail throttles and eventually blocks a sender that fires hundreds of
        messages back to back, so the pause is what keeps a large reminder run
        from getting the project's account flagged.
        """
        sent = 0
        for index, user in enumerate(recipients, start=1):
            if await self._email.send(
                to=user.email,
                template="study_reminder",
                context={"full_name": user.full_name},
            ):
                sent += 1
            if index % self._email_batch_size == 0 and index < len(recipients):
                await self._sleep(self._email_batch_pause_seconds)
        return sent


def local_day_start(now_local: datetime) -> datetime:
    """Midnight of the learner's current day, keeping the timezone attached."""
    return now_local.replace(hour=0, minute=0, second=0, microsecond=0)
