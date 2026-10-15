"""Functions 8.3 (view), 8.4 (delete) and 8.5 (toggle)."""

import uuid

import pytest
from notification.repositories.message_repository import MessageRepository
from notification.repositories.setting_repository import SettingRepository
from notification.services.notification_service import NotificationService
from sqlalchemy import text

OWNER = uuid.uuid4()
STRANGER = uuid.uuid4()


def headers(user_id: uuid.UUID = OWNER, tier: str = "normal") -> dict[str, str]:
    """Identity headers as the gateway forwards them."""
    return {"X-User-Id": str(user_id), "X-User-Roles": "CUSTOMER", "X-User-Tier": tier}


def make_service(session) -> NotificationService:
    return NotificationService(
        messages=MessageRepository(session), settings=SettingRepository(session)
    )


@pytest.fixture
async def seeded(session):
    """Three notifications for OWNER (one read) and one for STRANGER."""
    svc = make_service(session)
    rows = [
        await svc.create(user_id=OWNER, title="Thông báo 1", content="Nội dung 1"),
        await svc.create(user_id=OWNER, title="Thông báo 2", content="Nội dung 2"),
        await svc.create(user_id=OWNER, title="Thông báo 3", content="Nội dung 3"),
    ]
    other = await svc.create(user_id=STRANGER, title="Của người khác", content="x")
    await svc.mark_read(user_id=OWNER, message_id=rows[0].id)
    await session.commit()
    return {"owner": rows, "stranger": other}


# --------------------------------------------------------------------------
# 8.3 — view
# --------------------------------------------------------------------------


async def test_lists_only_the_callers_own_notifications(api_client, seeded):
    response = await api_client.get("/api/v1/notifications", headers=headers())

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert "Của người khác" not in {item["title"] for item in body["items"]}


async def test_reports_unread_count_for_the_badge(api_client, seeded):
    body = (await api_client.get("/api/v1/notifications", headers=headers())).json()

    # Three notifications, one of which the fixture marked read.
    assert body["unread_count"] == 2


async def test_unread_only_filters_and_narrows_total(api_client, seeded):
    body = (
        await api_client.get("/api/v1/notifications?unread_only=true", headers=headers())
    ).json()

    assert body["total"] == 2
    assert all(item["is_read"] is False for item in body["items"])


async def test_paginates_without_repeating_a_row(api_client, seeded):
    first = (await api_client.get("/api/v1/notifications?page=1&size=2", headers=headers())).json()
    second = (await api_client.get("/api/v1/notifications?page=2&size=2", headers=headers())).json()

    assert len(first["items"]) == 2
    assert len(second["items"]) == 1
    # The fixture inserts all three rows in one transaction, so created_at can
    # be identical — the id tie-breaker is what keeps the pages disjoint.
    assert {i["id"] for i in first["items"]}.isdisjoint({i["id"] for i in second["items"]})
    assert first["total"] == 3


async def test_rejects_an_oversized_page(api_client, seeded):
    response = await api_client.get("/api/v1/notifications?size=500", headers=headers())

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_requires_the_gateway_identity_header(api_client, seeded):
    response = await api_client.get("/api/v1/notifications")

    assert response.status_code == 401


async def test_marks_one_notification_read(api_client, seeded):
    target = seeded["owner"][1].id

    response = await api_client.patch(f"/api/v1/notifications/{target}/read", headers=headers())

    assert response.status_code == 204
    body = (await api_client.get("/api/v1/notifications", headers=headers())).json()
    assert body["unread_count"] == 1


async def test_marking_read_twice_is_idempotent(api_client, seeded):
    url = f"/api/v1/notifications/{seeded['owner'][1].id}/read"

    assert (await api_client.patch(url, headers=headers())).status_code == 204
    assert (await api_client.patch(url, headers=headers())).status_code == 204


async def test_cannot_mark_another_users_notification_read(api_client, seeded):
    response = await api_client.patch(
        f"/api/v1/notifications/{seeded['stranger'].id}/read", headers=headers()
    )

    assert response.status_code == 404


async def test_marks_everything_read(api_client, seeded):
    response = await api_client.patch("/api/v1/notifications/read-all", headers=headers())

    assert response.status_code == 200
    assert response.json()["updated"] == 2  # only the two unread ones
    body = (await api_client.get("/api/v1/notifications", headers=headers())).json()
    assert body["unread_count"] == 0


# --------------------------------------------------------------------------
# 8.4 — delete
# --------------------------------------------------------------------------


async def test_deletes_own_notification(api_client, seeded):
    target = seeded["owner"][0].id

    response = await api_client.delete(f"/api/v1/notifications/{target}", headers=headers())

    assert response.status_code == 204
    body = (await api_client.get("/api/v1/notifications", headers=headers())).json()
    assert body["total"] == 2
    assert target not in {uuid.UUID(i["id"]) for i in body["items"]}


async def test_cannot_delete_another_users_notification(api_client, seeded, session):
    stranger_id = seeded["stranger"].id

    response = await api_client.delete(f"/api/v1/notifications/{stranger_id}", headers=headers())

    assert response.status_code == 404
    # The row must still be there — a 404 that silently deleted would be worse
    # than a 403.
    items, _, _ = await make_service(session).list_for_user(
        user_id=STRANGER, page=1, size=10, unread_only=False
    )
    assert stranger_id in {m.id for m in items}


async def test_deleting_an_unknown_id_returns_404(api_client, seeded):
    response = await api_client.delete(f"/api/v1/notifications/{uuid.uuid4()}", headers=headers())

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


# --------------------------------------------------------------------------
# 8.5 — toggle
# --------------------------------------------------------------------------


async def test_reads_defaults_without_creating_a_row(api_client, session):
    response = await api_client.get("/api/v1/notifications/settings", headers=headers())

    assert response.status_code == 200
    assert response.json()["enable_daily_reminder"] is True
    # Reading preferences must not write: the account service would otherwise
    # have to seed a row for every registration.
    assert await make_service(session).get_settings(OWNER) is None


async def test_turns_the_daily_reminder_off_and_back_on(api_client):
    off = await api_client.put(
        "/api/v1/notifications/settings",
        json={"enable_daily_reminder": False},
        headers=headers(),
    )
    assert off.status_code == 200
    assert off.json()["enable_daily_reminder"] is False

    read_back = await api_client.get("/api/v1/notifications/settings", headers=headers())
    assert read_back.json()["enable_daily_reminder"] is False

    on = await api_client.put(
        "/api/v1/notifications/settings",
        json={"enable_daily_reminder": True},
        headers=headers(),
    )
    assert on.json()["enable_daily_reminder"] is True


async def test_writing_settings_twice_does_not_break_on_the_primary_key(api_client):
    payload = {"enable_daily_reminder": False}

    first = await api_client.put("/api/v1/notifications/settings", json=payload, headers=headers())
    second = await api_client.put("/api/v1/notifications/settings", json=payload, headers=headers())

    assert first.status_code == 200
    assert second.status_code == 200


async def test_settings_are_per_user(api_client):
    await api_client.put(
        "/api/v1/notifications/settings",
        json={"enable_daily_reminder": False},
        headers=headers(OWNER),
    )

    stranger_view = await api_client.get(
        "/api/v1/notifications/settings", headers=headers(STRANGER)
    )

    assert stranger_view.json()["enable_daily_reminder"] is True


async def test_device_token_survives_a_settings_write(api_client, session):
    """The web client must not be able to wipe the mobile push token."""
    await make_service(session).update_settings(user_id=OWNER, enable_daily_reminder=True)
    await session.execute(
        text(
            "update notification.settings set device_token = 'ExpoToken[abc]' where user_id = :uid"
        ),
        {"uid": OWNER},
    )
    await session.commit()

    await api_client.put(
        "/api/v1/notifications/settings",
        json={"enable_daily_reminder": False},
        headers=headers(),
    )

    response = await api_client.get("/api/v1/notifications/settings", headers=headers())
    assert response.json()["device_token"] == "ExpoToken[abc]"
