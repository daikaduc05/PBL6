"""Renders an email from a template and hands it to a transport.

Best-effort by design (notif_spec §5.5): a send that fails is logged and
reported as False, never raised. ``notification.messages`` is the source of
truth for what a user was told — email is the secondary channel, so a dead
SMTP server must not roll back the in-app notification that already succeeded.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from jinja2 import (
    Environment,
    PackageLoader,
    StrictUndefined,
    TemplateError,
    select_autoescape,
)

from notification.email.sender import EmailSender, EmailSendError, OutgoingEmail

logger = logging.getLogger(__name__)

# Waiting between attempts rather than hammering: most SMTP failures are
# transient (connection reset, greylisting, a brief rate limit).
DEFAULT_RETRY_DELAYS: tuple[float, ...] = (1.0, 5.0, 25.0)


@dataclass(frozen=True)
class EmailTemplate:
    file: str
    subject: str
    heading: str


# Subject and heading live here, not in the template files, so the cron job and
# the consumer cannot drift apart on wording.
TEMPLATES: dict[str, EmailTemplate] = {
    "study_reminder": EmailTemplate(
        file="study_reminder.html",
        subject="Đã đến giờ học hôm nay",
        heading="Giữ nhịp học của bạn",
    ),
    "vip_confirmed": EmailTemplate(
        file="vip_confirmed.html",
        subject="Thanh toán thành công",
        heading="Cảm ơn bạn đã nâng cấp",
    ),
}


def make_jinja_env() -> Environment:
    return Environment(
        loader=PackageLoader("notification.email", "templates"),
        # Autoescape is not optional here: full_name comes from user input, and
        # a name containing markup would otherwise be injected into the email.
        autoescape=select_autoescape(["html"]),
        # Strict so a forgotten context key raises instead of rendering an
        # empty string — "Chào ," reaching a real inbox is worse than no mail.
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


class EmailService:
    def __init__(
        self,
        sender: EmailSender,
        *,
        app_url: str,
        env: Environment | None = None,
        retry_delays: tuple[float, ...] = DEFAULT_RETRY_DELAYS,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._sender = sender
        self._app_url = app_url
        self._env = env or make_jinja_env()
        self._retry_delays = retry_delays
        # Injected so tests exercise the retry loop without actually waiting.
        self._sleep = sleep

    def render(self, template_name: str, context: dict[str, Any]) -> OutgoingEmail:
        """Build the message without sending it. Raises KeyError on a bad name."""
        template = TEMPLATES[template_name]
        html = self._env.get_template(template.file).render(
            subject=template.subject,
            heading=template.heading,
            app_url=self._app_url,
            **context,
        )
        return OutgoingEmail(to=context["to"], subject=template.subject, html=html)

    async def send(self, *, to: str, template: str, context: dict[str, Any]) -> bool:
        """Render and send. Returns False instead of raising on failure.

        Attempts once, then once more per entry in ``retry_delays``.
        """
        try:
            message = self.render(template, {**context, "to": to})
        except (KeyError, TemplateError):
            # An unknown template name or a missing context key is a
            # programming error; retrying cannot fix it, so fail loudly here
            # rather than mailing a half-rendered message to a real person.
            logger.exception("email: cannot render template %r", template)
            return False

        for attempt, delay in enumerate((*self._retry_delays, None), start=1):
            try:
                await self._sender.send(message)
                return True
            except EmailSendError as exc:
                if delay is None:
                    logger.error(
                        "email: giving up on %r to %s after %d attempts: %s",
                        template,
                        to,
                        attempt,
                        exc,
                    )
                    return False
                logger.warning(
                    "email: attempt %d for %r failed (%s), retrying in %ss",
                    attempt,
                    template,
                    exc,
                    delay,
                )
                await self._sleep(delay)

        return False  # unreachable; keeps the type checker happy
