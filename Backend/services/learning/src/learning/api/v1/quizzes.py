from uuid import UUID

from fastapi import APIRouter, Depends, status
from learning.deps import get_quiz_service
from learning.schemas.quiz import (
    QuizAdminResponse,
    QuizCreate,
    QuizStudentResponse,
)
from learning.schemas.submission import (
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from learning.services.quiz_service import QuizService
from pbl6_common.deps import UserContext, get_current_user, require_role

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@router.get("/lesson/{lesson_id}", response_model=QuizStudentResponse)
async def get_quiz_by_lesson(
    lesson_id: UUID,
    _user: UserContext = Depends(get_current_user),
    service: QuizService = Depends(get_quiz_service),
) -> QuizStudentResponse:
    """Retrieve quiz by lesson_id for students with correct answers stripped (T41)."""
    return await service.get_quiz_by_lesson_id(lesson_id)


@router.get("/{id}", response_model=QuizStudentResponse)
async def get_quiz(
    id: UUID,
    _user: UserContext = Depends(get_current_user),
    service: QuizService = Depends(get_quiz_service),
) -> QuizStudentResponse:
    """Retrieve quiz by quiz_id or lesson_id with correct answers stripped (T41)."""
    return await service.get_quiz_for_student(id)


@router.post("/{id}/submit", response_model=QuizSubmitResponse)
async def submit_quiz(
    id: UUID,
    req: QuizSubmitRequest,
    user: UserContext = Depends(get_current_user),
    service: QuizService = Depends(get_quiz_service),
) -> QuizSubmitResponse:
    """Submit quiz answers, compute score, save attempt history, and return result (T42)."""
    return await service.submit_quiz(
        user_id=UUID(user.user_id),
        quiz_id=id,
        req=req,
    )


@router.post("", response_model=QuizAdminResponse, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    data: QuizCreate,
    _user: UserContext = Depends(require_role("admin", "editor")),
    service: QuizService = Depends(get_quiz_service),
) -> QuizAdminResponse:
    """Create a new quiz with questions and options (Editor / Admin only)."""
    return await service.create_quiz(data)
