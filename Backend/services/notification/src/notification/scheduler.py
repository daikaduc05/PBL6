"""Hourly trigger for the study reminder (function 8.1).

Runs at minute 0 of every hour rather than once at 20:00, because each learner
chooses their own hour. Each pass only touches the people who asked for the
hour that just started, so twenty-four cheap passes replace one big one.
"""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from notification.config import NotificationSettings
from notification.repositories.external_reader import ExternalReader
from notification.repositories.message_repository import MessageRepository
from notification.repositories.setting_repository import SettingRepository
from notification.services.email_service import EmailService
from notification.services.reminder_service import ReminderService, local_day_start

logger = logging.getLogger(__name__)

REMINDER_JOB_ID = "study_reminder_hourly"


async def run_reminder_pass(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    email_service: EmailService,
    settings: NotificationSettings,
    now_local: datetime | None = None,
) -> None:
    """One hourly pass. Never raises — a failure must not kill the scheduler."""
    tz = ZoneInfo(settings.reminder_timezone)
    now = now_local or datetime.now(tz)

    try:
        async with session_factory() as session:
            service = ReminderService(
                messages=MessageRepository(session),
                settings=SettingRepository(session),
                external=ExternalReader(session),
                email=email_service,
                email_batch_size=settings.email_batch_size,
                email_batch_pause_seconds=settings.email_batch_pause_seconds,
            )
            # Notifications are committed before any email leaves, so an
            # interrupted mailing cannot produce duplicates on the next pass.
            run = await service.run(hour=now.hour, day_start=local_day_start(now))
            await session.commit()
            logger.info("study reminder pass finished: %s", run)
    except Exception:
        # APScheduler swallows exceptions quietly; logging here is the only way
        # anyone finds out a nightly job has been failing.
        logger.exception("study reminder pass failed for hour %s", now.hour)


def create_scheduler(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    email_service: EmailService,
    settings: NotificationSettings,
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=ZoneInfo(settings.reminder_timezone))
    scheduler.add_job(
        run_reminder_pass,
        CronTrigger(minute=0, timezone=ZoneInfo(settings.reminder_timezone)),
        id=REMINDER_JOB_ID,
        kwargs={
            "session_factory": session_factory,
            "email_service": email_service,
            "settings": settings,
        },
        # A pass that overruns must not be joined by the next one — two
        # concurrent passes would both see "not reminded yet" and double-send.
        max_instances=1,
        # If the process was asleep through several hours, run once rather than
        # firing every missed hour in a burst.
        coalesce=True,
        misfire_grace_time=600,
    )
    return scheduler
