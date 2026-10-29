from uuid import UUID

from learning.models.quiz import Option, Question, Quiz
from learning.schemas.quiz import QuizCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class QuizRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, quiz_id: UUID) -> Quiz | None:
        query = (
            select(Quiz)
            .where(Quiz.id == quiz_id)
            .options(selectinload(Quiz.questions).selectinload(Question.options))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_lesson_id(self, lesson_id: UUID) -> Quiz | None:
        query = (
            select(Quiz)
            .where(Quiz.lesson_id == lesson_id)
            .options(selectinload(Quiz.questions).selectinload(Question.options))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_or_lesson_id(self, identifier: UUID) -> Quiz | None:
        quiz = await self.get_by_id(identifier)
        if not quiz:
            quiz = await self.get_by_lesson_id(identifier)
        return quiz

    async def create(self, data: QuizCreate) -> Quiz:
        quiz = Quiz(lesson_id=data.lesson_id, title=data.title)
        for q_data in data.questions:
            question = Question(content=q_data.content, type=q_data.type)
            for opt_data in q_data.options:
                option = Option(content=opt_data.content, is_correct=opt_data.is_correct)
                question.options.append(option)
            quiz.questions.append(question)

        self.db.add(quiz)
        await self.db.commit()
        await self.db.refresh(quiz)
        return await self.get_by_id(quiz.id)  # type: ignore[return-value]
