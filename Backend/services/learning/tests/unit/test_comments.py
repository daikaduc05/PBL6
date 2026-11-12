from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from learning.deps import get_comment_repo
from learning.main import app
from learning.models.comment import Comment


class FakeCommentRepository:
    def __init__(self):
        self._comments: dict[uuid.UUID, Comment] = {}

    async def get_by_id(self, comment_id: uuid.UUID) -> Comment | None:
        return self._comments.get(comment_id)

    async def list_by_lesson(self, lesson_id: uuid.UUID) -> list[Comment]:
        return [c for c in self._comments.values() if c.lesson_id == lesson_id]

    async def create(self, comment: Comment) -> Comment:
        if not comment.id:
            comment.id = uuid.uuid4()
        if not comment.created_at:
            comment.created_at = datetime.now(UTC)
        self._comments[comment.id] = comment
        return comment

    async def delete(self, comment: Comment) -> None:
        self._comments.pop(comment.id, None)


@pytest.fixture
def fake_comment_repo():
    return FakeCommentRepository()


@pytest.fixture
def client(fake_comment_repo):
    app.dependency_overrides[get_comment_repo] = lambda: fake_comment_repo
    yield AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_comment_and_replies(client, fake_comment_repo):
    user_id = str(uuid.uuid4())
    lesson_id = str(uuid.uuid4())
    headers = {"X-User-Id": user_id, "X-User-Roles": "student"}

    # 1. Post a top-level comment
    res = await client.post(
        f"/api/v1/lessons/{lesson_id}/comments",
        headers=headers,
        json={"content": "Bài học rất hay và dễ hiểu!"},
    )
    assert res.status_code == 201
    comment_data = res.json()
    assert comment_data["content"] == "Bài học rất hay và dễ hiểu!"
    assert comment_data["user_id"] == user_id
    assert comment_data["parent_id"] is None
    comment_id = comment_data["id"]

    # 2. Post a reply to this comment
    reply_user_id = str(uuid.uuid4())
    reply_headers = {"X-User-Id": reply_user_id, "X-User-Roles": "student"}
    res_reply = await client.post(
        f"/api/v1/lessons/{lesson_id}/comments",
        headers=reply_headers,
        json={"content": "Đồng quan điểm với bạn!", "parent_id": comment_id},
    )
    assert res_reply.status_code == 201
    reply_data = res_reply.json()
    assert reply_data["parent_id"] == comment_id

    # 3. List comments for this lesson
    res_list = await client.get(f"/api/v1/lessons/{lesson_id}/comments")
    assert res_list.status_code == 200
    tree = res_list.json()
    assert len(tree) == 1
    assert tree[0]["id"] == comment_id
    assert len(tree[0]["replies"]) == 1
    assert tree[0]["replies"][0]["id"] == reply_data["id"]


@pytest.mark.asyncio
async def test_delete_comment_permissions(client, fake_comment_repo):
    user_id = str(uuid.uuid4())
    other_user_id = str(uuid.uuid4())
    lesson_id = str(uuid.uuid4())

    # Create comment
    c = Comment(
        id=uuid.uuid4(),
        lesson_id=uuid.UUID(lesson_id),
        user_id=uuid.UUID(user_id),
        content="Test delete permission",
        created_at=datetime.now(UTC),
    )
    await fake_comment_repo.create(c)

    # 1. Another student attempts to delete -> 403 Forbidden
    res = await client.delete(
        f"/api/v1/comments/{c.id}",
        headers={"X-User-Id": other_user_id, "X-User-Roles": "student"},
    )
    assert res.status_code == 403

    # 2. Admin can delete any comment -> 204
    admin_id = str(uuid.uuid4())
    res_admin = await client.delete(
        f"/api/v1/comments/{c.id}",
        headers={"X-User-Id": admin_id, "X-User-Roles": "admin"},
    )
    assert res_admin.status_code == 204
    assert await fake_comment_repo.get_by_id(c.id) is None
