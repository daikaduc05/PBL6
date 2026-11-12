from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from learning.deps import get_favorite_repo
from learning.main import app
from learning.models.favorite import FavoriteLesson


class FakeFavoriteRepository:
    def __init__(self):
        self._favorites: dict[tuple[uuid.UUID, uuid.UUID], FavoriteLesson] = {}

    async def get_by_user_and_lesson(
        self, user_id: uuid.UUID, lesson_id: uuid.UUID
    ) -> FavoriteLesson | None:
        return self._favorites.get((user_id, lesson_id))

    async def list_by_user(self, user_id: uuid.UUID) -> list[FavoriteLesson]:
        return [fav for fav in self._favorites.values() if fav.user_id == user_id]

    async def add(self, user_id: uuid.UUID, lesson_id: uuid.UUID) -> FavoriteLesson:
        key = (user_id, lesson_id)
        if key in self._favorites:
            return self._favorites[key]
        fav = FavoriteLesson(
            user_id=user_id,
            lesson_id=lesson_id,
            created_at=datetime.now(UTC),
        )
        self._favorites[key] = fav
        return fav

    async def delete(self, user_id: uuid.UUID, lesson_id: uuid.UUID) -> bool:
        key = (user_id, lesson_id)
        if key in self._favorites:
            del self._favorites[key]
            return True
        return False


@pytest.fixture
def fake_favorite_repo():
    return FakeFavoriteRepository()


@pytest.fixture
def client(fake_favorite_repo):
    app.dependency_overrides[get_favorite_repo] = lambda: fake_favorite_repo
    yield AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_favorite_lifecycle(client, fake_favorite_repo):
    user_id = str(uuid.uuid4())
    lesson_id = str(uuid.uuid4())
    headers = {"X-User-Id": user_id, "X-User-Roles": "student"}

    # 1. Initial status: not favorite
    res_status = await client.get(
        f"/api/v1/lessons/{lesson_id}/favorite",
        headers=headers,
    )
    assert res_status.status_code == 200
    assert res_status.json()["is_favorite"] is False

    # 2. Add to favorites
    res_add = await client.post(
        f"/api/v1/lessons/{lesson_id}/favorite",
        headers=headers,
    )
    assert res_add.status_code == 201
    assert res_add.json()["lesson_id"] == lesson_id

    # 3. Status is now favorite
    res_status2 = await client.get(
        f"/api/v1/lessons/{lesson_id}/favorite",
        headers=headers,
    )
    assert res_status2.status_code == 200
    assert res_status2.json()["is_favorite"] is True

    # 4. List favorites includes this lesson
    res_list = await client.get("/api/v1/me/favorites", headers=headers)
    assert res_list.status_code == 200
    items = res_list.json()
    assert len(items) == 1
    assert items[0]["lesson_id"] == lesson_id

    # 5. Remove from favorites
    res_del = await client.delete(
        f"/api/v1/lessons/{lesson_id}/favorite",
        headers=headers,
    )
    assert res_del.status_code == 204

    # 6. Verify removed
    res_status3 = await client.get(
        f"/api/v1/lessons/{lesson_id}/favorite",
        headers=headers,
    )
    assert res_status3.status_code == 200
    assert res_status3.json()["is_favorite"] is False
