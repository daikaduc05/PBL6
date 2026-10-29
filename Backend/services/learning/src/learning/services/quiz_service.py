from uuid import UUID

from learning.models.quiz import Quiz
from learning.repositories.history_repository import HistoryRepository
from learning.repositories.quiz_repository import QuizRepository
from learning.schemas.quiz import (
    OptionAdminResponse,
    OptionStudentResponse,
    QuestionAdminResponse,
    QuestionStudentResponse,
    QuizAdminResponse,
    QuizCreate,
    QuizStudentResponse,
)
from learning.schemas.submission import (
    QuestionResult,
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from pbl6_common.errors import AppError, NotFoundError


class QuizService:
    def __init__(self, quiz_repo: QuizRepository, history_repo: HistoryRepository):
        self.quiz_repo = quiz_repo
        self.history_repo = history_repo

    def _to_student_response(self, quiz: Quiz) -> QuizStudentResponse:
        questions = []
        for q in quiz.questions:
            options = [OptionStudentResponse(id=opt.id, content=opt.content) for opt in q.options]
            questions.append(
                QuestionStudentResponse(
                    id=q.id,
                    content=q.content,
                    type=q.type,
                    options=options,
                )
            )
        return QuizStudentResponse(
            id=quiz.id,
            lesson_id=quiz.lesson_id,
            title=quiz.title,
            created_at=quiz.created_at,
            questions=questions,
        )

    def _to_admin_response(self, quiz: Quiz) -> QuizAdminResponse:
        questions = []
        for q in quiz.questions:
            options = [
                OptionAdminResponse(id=opt.id, content=opt.content, is_correct=opt.is_correct)
                for opt in q.options
            ]
            questions.append(
                QuestionAdminResponse(
                    id=q.id,
                    content=q.content,
                    type=q.type,
                    options=options,
                )
            )
        return QuizAdminResponse(
            id=quiz.id,
            lesson_id=quiz.lesson_id,
            title=quiz.title,
            created_at=quiz.created_at,
            questions=questions,
        )

    async def get_quiz_for_student(self, identifier: UUID) -> QuizStudentResponse:
        quiz = await self.quiz_repo.get_by_id_or_lesson_id(identifier)
        if not quiz:
            raise NotFoundError(f"Quiz not found for identifier {identifier}")
        return self._to_student_response(quiz)

    async def get_quiz_by_lesson_id(self, lesson_id: UUID) -> QuizStudentResponse:
        quiz = await self.quiz_repo.get_by_lesson_id(lesson_id)
        if not quiz:
            raise NotFoundError(f"Quiz not found for lesson {lesson_id}")
        return self._to_student_response(quiz)

    async def get_quiz_admin(self, quiz_id: UUID) -> QuizAdminResponse:
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            raise NotFoundError(f"Quiz not found with id {quiz_id}")
        return self._to_admin_response(quiz)

    async def create_quiz(self, data: QuizCreate) -> QuizAdminResponse:
        quiz = await self.quiz_repo.create(data)
        return self._to_admin_response(quiz)

    async def submit_quiz(
        self, user_id: UUID, quiz_id: UUID, req: QuizSubmitRequest
    ) -> QuizSubmitResponse:
        quiz = await self.quiz_repo.get_by_id(quiz_id)
        if not quiz:
            # Fallback check if identifier was lesson_id
            quiz = await self.quiz_repo.get_by_lesson_id(quiz_id)
            if not quiz:
                raise NotFoundError(f"Quiz not found with id {quiz_id}")

        if not quiz.questions:
            raise AppError("Quiz has no questions to evaluate")

        answers_map: dict[UUID, set[UUID]] = {
            ans.question_id: set(ans.selected_option_ids) for ans in req.answers
        }

        correct_count = 0
        results: list[QuestionResult] = []

        for q in quiz.questions:
            correct_option_ids = {opt.id for opt in q.options if opt.is_correct}
            selected_option_ids = answers_map.get(q.id, set())

            is_correct = bool(correct_option_ids and selected_option_ids == correct_option_ids)
            if is_correct:
                correct_count += 1

            results.append(
                QuestionResult(
                    question_id=q.id,
                    is_correct=is_correct,
                    selected_option_ids=list(selected_option_ids),
                    correct_option_ids=list(correct_option_ids),
                )
            )

        total_questions = len(quiz.questions)
        score = round((correct_count / total_questions) * 100.0, 1)

        history = await self.history_repo.upsert(
            user_id=user_id,
            lesson_id=quiz.lesson_id,
            score=score,
        )

        passed = score >= 80.0

        return QuizSubmitResponse(
            quiz_id=quiz.id,
            lesson_id=quiz.lesson_id,
            score=score,
            highest_score=history.highest_score,
            total_questions=total_questions,
            correct_answers_count=correct_count,
            passed=passed,
            completed_at=history.completed_at,
            results=results,
        )
