from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OptionStudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    content: str


class OptionAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    content: str
    is_correct: bool


class OptionCreate(BaseModel):
    content: str = Field(..., min_length=1)
    is_correct: bool = False


class QuestionStudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    content: str
    type: str
    options: list[OptionStudentResponse] = []


class QuestionAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    content: str
    type: str
    options: list[OptionAdminResponse] = []


class QuestionCreate(BaseModel):
    content: str = Field(..., min_length=1)
    type: str = Field(default="SINGLE_CHOICE", pattern="^(SINGLE_CHOICE|MULTI_CHOICE)$")
    options: list[OptionCreate] = Field(..., min_length=2)


class QuizCreate(BaseModel):
    lesson_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    questions: list[QuestionCreate] = []


class QuizStudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lesson_id: UUID
    title: str
    created_at: datetime
    questions: list[QuestionStudentResponse] = []


class QuizAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lesson_id: UUID
    title: str
    created_at: datetime
    questions: list[QuestionAdminResponse] = []
