"""Minimal SMTP sending — just enough for password-reset emails. Nothing
fancier (templates, retries, queueing) since this is the only email this
service sends; notification service (T15) owns the real email
infrastructure for everything else.

`EmailSenderProtocol` lets services depend on "something that sends
email" without pulling in smtplib, so unit tests inject a fake instead of
needing a real SMTP server — same pattern as
account.events.publisher.EventPublisherProtocol.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from typing import Protocol

from account.config import AccountSettings

logger = logging.getLogger(__name__)


class EmailSenderProtocol(Protocol):
    async def send(self, *, to: str, subject: str, body: str) -> None: ...


class SmtpEmailSender:
    def __init__(self, settings: AccountSettings):
        self._settings = settings

    async def send(self, *, to: str, subject: str, body: str) -> None:
        # smtplib is blocking — off the event loop so one slow SMTP
        # round-trip doesn't stall every other request this service is
        # handling.
        await asyncio.to_thread(self._send_sync, to, subject, body)

    def _send_sync(self, to: str, subject: str, body: str) -> None:
        settings = self._settings
        message = MIMEText(body, "plain", "utf-8")
        message["Subject"] = subject
        message["From"] = f"{settings.smtp_from_name} <{settings.smtp_user}>"
        message["To"] = to

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)
