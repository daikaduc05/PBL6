"""T15 — rendering and the retry policy (function 8.1, email half)."""

import pytest
from notification.email.sender import EmailSendError, OutgoingEmail
from notification.services.email_service import EmailService

APP_URL = "https://pbl6.test"


class FakeSender:
    """Records what it was asked to send; fails the first `fail_times` calls."""

    def __init__(self, fail_times: int = 0) -> None:
        self.fail_times = fail_times
        self.sent: list[OutgoingEmail] = []
        self.attempts = 0

    async def send(self, message: OutgoingEmail) -> None:
        self.attempts += 1
        if self.attempts <= self.fail_times:
            raise EmailSendError("simulated transport failure")
        self.sent.append(message)


def make_service(sender: FakeSender, **kwargs) -> tuple[EmailService, list[float]]:
    """Service whose sleep is recorded instead of actually waiting."""
    slept: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    service = EmailService(sender, app_url=APP_URL, sleep=fake_sleep, **kwargs)
    return service, slept


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


async def test_renders_the_vip_expired_renewal_nudge():
    """The one email a lapsed user still receives — it must carry the local
    expiry time it was given and point at the checkout page."""
    sender = FakeSender()
    service, _ = make_service(sender)

    assert await service.send(
        to="lapsed@example.com",
        template="vip_expired",
        context={"full_name": "Lan", "expired_on": "00:00 ngày 09/11/2026"},
    )

    message = sender.sent[0]
    assert message.subject == "Gói VIP đã hết hạn"
    assert "00:00 ngày 09/11/2026" in message.html
    assert f"{APP_URL}/checkout" in message.html


async def test_renders_the_study_reminder_with_name_and_link():
    sender = FakeSender()
    service, _ = make_service(sender)

    assert await service.send(
        to="hoc.vien@example.com", template="study_reminder", context={"full_name": "Minh"}
    )

    message = sender.sent[0]
    assert message.to == "hoc.vien@example.com"
    assert message.subject == "Đã đến giờ học hôm nay"
    assert "Minh" in message.html
    assert f"{APP_URL}/lessons" in message.html


async def test_vip_email_avoids_promising_immediate_access():
    """VIP is eventually consistent — the mail must not claim otherwise."""
    sender = FakeSender()
    service, _ = make_service(sender)

    await service.send(
        to="vip@example.com",
        template="vip_confirmed",
        context={
            "full_name": "Lan",
            "plan_name": "VIP 1 tháng",
            "amount_vnd": 199000,
            "duration_days": 30,
        },
    )

    html = sender.sent[0].html
    assert "199,000" in html
    assert "ít phút" in html  # "will be activated shortly", not "you are VIP now"


async def test_escapes_html_in_user_supplied_names():
    """full_name comes from the account service, which got it from a form."""
    sender = FakeSender()
    service, _ = make_service(sender)

    await service.send(
        to="a@example.com",
        template="study_reminder",
        context={"full_name": "<script>alert(1)</script>"},
    )

    html = sender.sent[0].html
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


async def test_unknown_template_fails_without_raising():
    sender = FakeSender()
    service, _ = make_service(sender)

    assert await service.send(to="a@example.com", template="does_not_exist", context={}) is False
    assert sender.attempts == 0


async def test_missing_context_key_fails_without_sending():
    sender = FakeSender()
    service, _ = make_service(sender)

    # study_reminder needs full_name. StrictUndefined turns the omission into
    # an error, so nothing goes out — better than mailing "Chào ," to someone.
    assert await service.send(to="a@example.com", template="study_reminder", context={}) is False
    assert sender.attempts == 0


# --------------------------------------------------------------------------
# Retry policy
# --------------------------------------------------------------------------


async def test_retries_then_succeeds():
    sender = FakeSender(fail_times=2)
    service, slept = make_service(sender, retry_delays=(1.0, 5.0, 25.0))

    assert await service.send(
        to="a@example.com", template="study_reminder", context={"full_name": "A"}
    )

    assert sender.attempts == 3
    assert slept == [1.0, 5.0]  # no wait after the attempt that worked


async def test_gives_up_after_the_configured_attempts():
    sender = FakeSender(fail_times=99)
    service, slept = make_service(sender, retry_delays=(1.0, 5.0, 25.0))

    result = await service.send(
        to="a@example.com", template="study_reminder", context={"full_name": "A"}
    )

    # One initial attempt plus one per delay, then it stops rather than raising:
    # a dead SMTP server must not roll back the in-app notification.
    assert result is False
    assert sender.attempts == 4
    assert slept == [1.0, 5.0, 25.0]


@pytest.mark.parametrize("delays", [(), (0.1,)])
async def test_retry_count_follows_configuration(delays):
    sender = FakeSender(fail_times=99)
    service, _ = make_service(sender, retry_delays=delays)

    await service.send(to="a@example.com", template="study_reminder", context={"full_name": "A"})

    assert sender.attempts == len(delays) + 1
