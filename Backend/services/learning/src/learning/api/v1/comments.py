from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from learning.deps import get_comment_service
from learning.schemas.comment import CommentCreate, CommentResponse
from learning.services.comment_service import CommentService
from pbl6_common.deps import UserContext, get_current_user

router = APIRouter(tags=["comments"])


@router.get("/lessons/{lesson_id}/comments", response_model=list[CommentResponse])
async def get_lesson_comments(
    lesson_id: UUID,
    service: CommentService = Depends(get_comment_service),
) -> list[CommentResponse]:
    """Get all comments and nested replies for a lesson (T48)."""
    return await service.get_lesson_comments(lesson_id)


@router.post(
    "/lessons/{lesson_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    lesson_id: UUID,
    body: CommentCreate,
    user: UserContext = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
) -> CommentResponse:
    """Post a comment or reply to a comment on a lesson (T48)."""
    return await service.add_comment(lesson_id, UUID(user.user_id), body)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    user: UserContext = Depends(get_current_user),
    service: CommentService = Depends(get_comment_service),
) -> None:
    """Delete a comment (must be comment author, editor or admin) (T48)."""
    await service.delete_comment(comment_id, UUID(user.user_id), user.roles)
