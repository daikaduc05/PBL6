from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from learning.deps import get_history_repo, get_quiz_repo
from learning.main import app
from learning.models.history import History
from learning.models.quiz import Option, Question, Quiz
from learning.schemas.quiz import QuizCreate


class FakeQuizRepository:
    def __init__(self):
        self._by_id: dict[uuid.UUID, Quiz] = {}
        self._by_lesson: dict[uuid.UUID, Quiz] = {}

    async def get_by_id(self, quiz_id: uuid.UUID) -> Quiz | None:
        return self._by_id.get(quiz_id)

    async def get_by_lesson_id(self, lesson_id: uuid.UUID) -> Quiz | None:
        return self._by_lesson.get(lesson_id)

    async def get_by_id_or_lesson_id(self, identifier: uuid.UUID) -> Quiz | None:
        return self._by_id.get(identifier) or self._by_lesson.get(identifier)

    async def create(self, data: QuizCreate) -> Quiz:
        quiz = Quiz(
            id=uuid.uuid4(),
            lesson_id=data.lesson_id,
            title=data.title,
            created_at=datetime.now(UTC),
        )
        for q_data in data.questions:
            q = Question(
                id=uuid.uuid4(),
                quiz_id=quiz.id,
                content=q_data.content,
                type=q_data.type,
            )
            for opt_data in q_data.options:
                opt = Option(
                    id=uuid.uuid4(),
                    question_id=q.id,
                    content=opt_data.content,
                    is_correct=opt_data.is_correct,
                )
                q.options.append(opt)
            quiz.questions.append(q)

        self._by_id[quiz.id] = quiz
        self._by_lesson[quiz.lesson_id] = quiz
        return quiz


class FakeHistoryRepository:
    def __init__(self):
        self._histories: dict[tuple[uuid.UUID, uuid.UUID], History] = {}

    async def get_by_user_and_lesson(
        self, user_id: uuid.UUID, lesson_id: uuid.UUID
    ) -> History | None:
        return self._histories.get((user_id, lesson_id))

    async def upsert(self, user_id: uuid.UUID, lesson_id: uuid.UUID, score: float) -> History:
        key = (user_id, lesson_id)
        existing = self._histories.get(key)
        now = datetime.now(UTC)
        if existing:
            existing.highest_score = max(existing.highest_score, score)
            existing.completed_at = now
            return existing

        hist = History(
            id=uuid.uuid4(),
            user_id=user_id,
            lesson_id=lesson_id,
            highest_score=score,
            completed_at=now,
        )
        self._histories[key] = hist
        return hist

    async def list_by_user(self, user_id: uuid.UUID) -> list[History]:
        return [h for h in self._histories.values() if h.user_id == user_id]

    async def get_last_activity_for_user(self, user_id: uuid.UUID) -> History | None:
        user_hists = [h for h in self._histories.values() if h.user_id == user_id]
        if not user_hists:
            return None
        return max(user_hists, key=lambda h: h.completed_at)

    async def get_last_activities(
        self, since: datetime | None = None, limit: int = 1000
    ) -> list[History]:
        results: dict[uuid.UUID, History] = {}
        for h in self._histories.values():
            if since and h.completed_at < since:
                continue
            if h.user_id not in results or results[h.user_id].completed_at < h.completed_at:
                results[h.user_id] = h
        return list(results.values())[:limit]


@pytest.fixture
def fake_repos():
    quiz_repo = FakeQuizRepository()
    history_repo = FakeHistoryRepository()

    app.dependency_overrides[get_quiz_repo] = lambda: quiz_repo
    app.dependency_overrides[get_history_repo] = lambda: history_repo

    yield quiz_repo, history_repo

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_t41_get_quiz_anonymous_rejected(fake_repos):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/v1/quizzes/{uuid.uuid4()}")
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_api_t41_and_t42_full_quiz_flow(fake_repos):
    quiz_repo, _ = fake_repos
    lesson_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # Pre-populate a quiz
    quiz = Quiz(
        id=uuid.uuid4(),
        lesson_id=lesson_id,
        title="Grammar Level 1",
        created_at=datetime.now(UTC),
    )
    q1 = Question(id=uuid.uuid4(), quiz_id=quiz.id, content="Choose the verb", type="SINGLE_CHOICE")
    opt_run = Option(id=uuid.uuid4(), question_id=q1.id, content="run", is_correct=True)
    opt_table = Option(id=uuid.uuid4(), question_id=q1.id, content="table", is_correct=False)
    q1.options = [opt_run, opt_table]
    quiz.questions = [q1]

    quiz_repo._by_id[quiz.id] = quiz
    quiz_repo._by_lesson[lesson_id] = quiz

    headers = {
        "X-User-Id": str(user_id),
        "X-User-Roles": "student",
        "X-User-Tier": "normal",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. T41: GET /api/v1/quizzes/{id}
        resp = await client.get(f"/api/v1/quizzes/{quiz.id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Grammar Level 1"
        assert len(data["questions"]) == 1
        # Confirm no 'is_correct' field in options
        for opt in data["questions"][0]["options"]:
            assert "is_correct" not in opt

        # 2. T41: GET /api/v1/quizzes/lesson/{lesson_id}
        resp_by_lesson = await client.get(f"/api/v1/quizzes/lesson/{lesson_id}", headers=headers)
        assert resp_by_lesson.status_code == 200
        assert resp_by_lesson.json()["id"] == str(quiz.id)

        # 3. T42: POST /api/v1/quizzes/{id}/submit
        submit_payload = {
            "answers": [
                {
                    "question_id": str(q1.id),
                    "selected_option_ids": [str(opt_run.id)],
                }
            ],
            "duration_seconds": 12,
        }
        submit_resp = await client.post(
            f"/api/v1/quizzes/{quiz.id}/submit",
            json=submit_payload,
            headers=headers,
        )
        assert submit_resp.status_code == 200
        res_data = submit_resp.json()
        assert res_data["score"] == 100.0
        assert res_data["passed"] is True
        assert res_data["correct_answers_count"] == 1

        # 4. GET /api/v1/me/attempts
        attempts_resp = await client.get("/api/v1/me/attempts", headers=headers)
        assert attempts_resp.status_code == 200
        attempts = attempts_resp.json()
        assert len(attempts) == 1
        assert attempts[0]["lesson_id"] == str(lesson_id)
        assert attempts[0]["highest_score"] == 100.0


@pytest.mark.asyncio
async def test_api_t43_last_activity(fake_repos):
    _, history_repo = fake_repos
    user_id = uuid.uuid4()
    lesson_id = uuid.uuid4()

    await history_repo.upsert(user_id, lesson_id, 95.0)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Internal endpoint with user_id
        resp_user = await client.get(f"/internal/learning/last-activity?user_id={user_id}")
        assert resp_user.status_code == 200
        user_data = resp_user.json()
        assert user_data["user_id"] == str(user_id)
        assert user_data["has_studied_today"] is True
        assert user_data["highest_score"] == 95.0

        # Internal endpoint without user_id (batch for cron)
        resp_batch = await client.get("/internal/learning/last-activity")
        assert resp_batch.status_code == 200
        batch_data = resp_batch.json()
        assert batch_data["total"] == 1
        assert batch_data["items"][0]["user_id"] == str(user_id)

        # Health checks
        health_resp = await client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["service"] == "learning"
