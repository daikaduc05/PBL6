from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AnswerSubmit(BaseModel):
    question_id: UUID
    selected_option_ids: list[UUID] = Field(default_factory=list)

    @field_validator("selected_option_ids", mode="before")
    @classmethod
    def coerce_single_to_list(cls, v):
        if isinstance(v, (str, UUID)):
            return [v]
        return v


class QuizSubmitRequest(BaseModel):
    answers: list[AnswerSubmit] = Field(..., min_length=1)
    duration_seconds: int | None = Field(default=None, ge=0)


class QuestionResult(BaseModel):
    question_id: UUID
    is_correct: bool
    selected_option_ids: list[UUID]
    correct_option_ids: list[UUID]


class QuizSubmitResponse(BaseModel):
    quiz_id: UUID
    lesson_id: UUID
    score: float
    highest_score: float
    total_questions: int
    correct_answers_count: int
    passed: bool
    completed_at: datetime
    results: list[QuestionResult]
