from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from learning.models.history import History
from learning.models.quiz import Option, Question, Quiz
from learning.schemas.quiz import OptionCreate, QuestionCreate, QuizCreate
from learning.schemas.submission import AnswerSubmit, QuizSubmitRequest
from learning.services.learning_service import LearningService
from learning.services.quiz_service import QuizService
from pbl6_common.errors import NotFoundError


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
def repos():
    return FakeQuizRepository(), FakeHistoryRepository()


@pytest.fixture
def sample_quiz_data() -> QuizCreate:
    lesson_id = uuid.uuid4()
    return QuizCreate(
        lesson_id=lesson_id,
        title="Unit 1 Practice Quiz",
        questions=[
            QuestionCreate(
                content="What is the capital of England?",
                type="SINGLE_CHOICE",
                options=[
                    OptionCreate(content="London", is_correct=True),
                    OptionCreate(content="Paris", is_correct=False),
                    OptionCreate(content="Berlin", is_correct=False),
                ],
            ),
            QuestionCreate(
                content="Which of these are fruits?",
                type="SINGLE_CHOICE",
                options=[
                    OptionCreate(content="Apple", is_correct=True),
                    OptionCreate(content="Carrot", is_correct=False),
                ],
            ),
        ],
    )


# --- T41 Tests: Quiz Retrieval & Answer Stripping ---


@pytest.mark.asyncio
async def test_t41_get_quiz_strips_answers(repos, sample_quiz_data):
    quiz_repo, history_repo = repos
    service = QuizService(quiz_repo, history_repo)

    created_quiz = await service.create_quiz(sample_quiz_data)
    student_quiz = await service.get_quiz_for_student(created_quiz.id)

    assert student_quiz.id == created_quiz.id
    assert student_quiz.title == "Unit 1 Practice Quiz"
    assert len(student_quiz.questions) == 2

    # Verify that is_correct attribute is completely stripped from OptionStudentResponse
    for question in student_quiz.questions:
        for option in question.options:
            assert not hasattr(option, "is_correct")


@pytest.mark.asyncio
async def test_t41_get_quiz_by_lesson_id(repos, sample_quiz_data):
    quiz_repo, history_repo = repos
    service = QuizService(quiz_repo, history_repo)

    await service.create_quiz(sample_quiz_data)
    student_quiz = await service.get_quiz_by_lesson_id(sample_quiz_data.lesson_id)

    assert student_quiz.lesson_id == sample_quiz_data.lesson_id
    assert len(student_quiz.questions) == 2


@pytest.mark.asyncio
async def test_t41_get_quiz_not_found(repos):
    quiz_repo, history_repo = repos
    service = QuizService(quiz_repo, history_repo)

    with pytest.raises(NotFoundError):
        await service.get_quiz_for_student(uuid.uuid4())


# --- T42 Tests: Quiz Submission & Scoring ---


@pytest.mark.asyncio
async def test_t42_submit_all_correct(repos, sample_quiz_data):
    quiz_repo, history_repo = repos
    service = QuizService(quiz_repo, history_repo)
    user_id = uuid.uuid4()

    quiz = await service.create_quiz(sample_quiz_data)

    # Prepare answers with all correct choices
    q1 = quiz.questions[0]
    q1_correct = [opt.id for opt in q1.options if opt.is_correct][0]
    q2 = quiz.questions[1]
    q2_correct = [opt.id for opt in q2.options if opt.is_correct][0]

    req = QuizSubmitRequest(
        answers=[
            AnswerSubmit(question_id=q1.id, selected_option_ids=[q1_correct]),
            AnswerSubmit(question_id=q2.id, selected_option_ids=[q2_correct]),
        ],
        duration_seconds=45,
    )

    result = await service.submit_quiz(user_id, quiz.id, req)

    assert result.score == 100.0
    assert result.highest_score == 100.0
    assert result.total_questions == 2
    assert result.correct_answers_count == 2
    assert result.passed is True
    assert all(r.is_correct for r in result.results)

    # Check history persistence
    hist = await history_repo.get_by_user_and_lesson(user_id, quiz.lesson_id)
    assert hist is not None
    assert hist.highest_score == 100.0


@pytest.mark.asyncio
async def test_t42_submit_partial_correct_and_highest_score(repos, sample_quiz_data):
    quiz_repo, history_repo = repos
    service = QuizService(quiz_repo, history_repo)
    user_id = uuid.uuid4()

    quiz = await service.create_quiz(sample_quiz_data)

    q1 = quiz.questions[0]
    q1_correct = [opt.id for opt in q1.options if opt.is_correct][0]
    q2 = quiz.questions[1]
    q2_wrong = [opt.id for opt in q2.options if not opt.is_correct][0]

    # Attempt 1: 1 of 2 correct = 50.0%
    req1 = QuizSubmitRequest(
        answers=[
            AnswerSubmit(question_id=q1.id, selected_option_ids=[q1_correct]),
            AnswerSubmit(question_id=q2.id, selected_option_ids=[q2_wrong]),
        ]
    )
    res1 = await service.submit_quiz(user_id, quiz.id, req1)
    assert res1.score == 50.0
    assert res1.highest_score == 50.0
    assert res1.passed is False

    # Attempt 2: 0 of 2 correct = 0.0%, highest_score should remain 50.0%
    q1_wrong = [opt.id for opt in q1.options if not opt.is_correct][0]
    req2 = QuizSubmitRequest(
        answers=[
            AnswerSubmit(question_id=q1.id, selected_option_ids=[q1_wrong]),
            AnswerSubmit(question_id=q2.id, selected_option_ids=[q2_wrong]),
        ]
    )
    res2 = await service.submit_quiz(user_id, quiz.id, req2)
    assert res2.score == 0.0
    assert res2.highest_score == 50.0


# --- T43 Tests: Last Activity & Cron Reminder Query ---


@pytest.mark.asyncio
async def test_t43_user_last_activity(repos):
    _, history_repo = repos
    learning_service = LearningService(history_repo)

    user1 = uuid.uuid4()
    user2 = uuid.uuid4()
    lesson1 = uuid.uuid4()

    # User 1 studied today
    await history_repo.upsert(user1, lesson1, 90.0)

    res1 = await learning_service.get_last_activity_for_user(user1)
    assert res1.user_id == user1
    assert res1.highest_score == 90.0
    assert res1.has_studied_today is True

    # User 2 has not studied yet
    res2 = await learning_service.get_last_activity_for_user(user2)
    assert res2.user_id == user2
    assert res2.has_studied_today is False
    assert res2.last_activity_at is None


@pytest.mark.asyncio
async def test_t43_batch_last_activities(repos):
    _, history_repo = repos
    learning_service = LearningService(history_repo)

    user1 = uuid.uuid4()
    user2 = uuid.uuid4()

    await history_repo.upsert(user1, uuid.uuid4(), 85.0)
    await history_repo.upsert(user2, uuid.uuid4(), 70.0)

    batch = await learning_service.get_last_activities()
    assert batch.total == 2
    user_ids = {item.user_id for item in batch.items}
    assert user_ids == {user1, user2}

    # Filter with future since should yield 0
    future = datetime.now(UTC) + timedelta(days=1)
    empty_batch = await learning_service.get_last_activities(since=future)
    assert empty_batch.total == 0
