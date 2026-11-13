"""Transports that put an email on the wire.

Only this module knows *how* mail leaves the process. Everything above it
(``EmailService``) builds the message and decides whether a failure matters,
so swapping Mailpit for Gmail or Resend is one environment variable.
"""

from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage as MimeMessage
from typing import Protocol

import aiosmtplib
import httpx

from notification.config import NotificationSettings

RESEND_ENDPOINT = "https://api.resend.com/emails"
SEND_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class OutgoingEmail:
    to: str
    subject: str
    html: str


class EmailSendError(Exception):
    """Transport failed. ``EmailService`` decides whether to retry."""


class EmailSender(Protocol):
    async def send(self, message: OutgoingEmail) -> None: ...


class SmtpSender:
    """Plain SMTP — Mailpit in development, Gmail for a demo.

    Gmail requires ``smtp_use_tls`` and an **app password**; a normal account
    password is rejected. Mailpit needs neither.
    """

    def __init__(
        self,
        *,
        host: str,
        port: int,
        from_addr: str,
        username: str = "",
        password: str = "",
        use_tls: bool = False,
    ) -> None:
        self._host = host
        self._port = port
        self._from = from_addr
        self._username = username
        self._password = password
        self._use_tls = use_tls

    async def send(self, message: OutgoingEmail) -> None:
        mime = MimeMessage()
        mime["From"] = self._from
        mime["To"] = message.to
        mime["Subject"] = message.subject
        mime.set_content(message.html, subtype="html")

        try:
            await aiosmtplib.send(
                mime,
                hostname=self._host,
                port=self._port,
                username=self._username or None,
                password=self._password or None,
                start_tls=self._use_tls,
                timeout=SEND_TIMEOUT_SECONDS,
            )
        except Exception as exc:  # noqa: BLE001 - any aiosmtplib error is a send failure
            raise EmailSendError(f"smtp send failed: {exc}") from exc


class ResendSender:
    """Resend's HTTP API.

    Note for whoever enables this: until the project's domain is verified,
    Resend only delivers to the address the account was registered with.
    """

    def __init__(self, *, api_key: str, from_addr: str) -> None:
        self._api_key = api_key
        self._from = from_addr

    async def send(self, message: OutgoingEmail) -> None:
        payload = {
            "from": self._from,
            "to": [message.to],
            "subject": message.subject,
            "html": message.html,
        }
        try:
            async with httpx.AsyncClient(timeout=SEND_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    RESEND_ENDPOINT,
                    json=payload,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise EmailSendError(f"resend send failed: {exc}") from exc


def make_sender(settings: NotificationSettings) -> EmailSender:
    if settings.email_provider == "resend":
        return ResendSender(api_key=settings.email_api_key, from_addr=settings.email_from)
    return SmtpSender(
        host=settings.smtp_host,
        port=settings.smtp_port,
        from_addr=settings.email_from,
        username=settings.smtp_username,
        password=settings.smtp_password,
        use_tls=settings.smtp_use_tls,
    )
