from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from learning.models.comment import Comment
from learning.repositories.comment_repository import CommentRepository
from learning.schemas.comment import CommentCreate, CommentResponse


class CommentService:
    def __init__(self, repo: CommentRepository):
        self.repo = repo

    async def get_lesson_comments(self, lesson_id: UUID) -> list[CommentResponse]:
        raw_comments = await self.repo.list_by_lesson(lesson_id)

        comment_map: dict[UUID, CommentResponse] = {}
        for c in raw_comments:
            comment_map[c.id] = CommentResponse(
                id=c.id,
                lesson_id=c.lesson_id,
                user_id=c.user_id,
                parent_id=c.parent_id,
                content=c.content,
                created_at=c.created_at,
                replies=[],
            )

        tree: list[CommentResponse] = []
        for c in raw_comments:
            node = comment_map[c.id]
            if c.parent_id is not None and c.parent_id in comment_map:
                comment_map[c.parent_id].replies.append(node)
            else:
                tree.append(node)

        return tree

    async def add_comment(
        self, lesson_id: UUID, user_id: UUID, data: CommentCreate
    ) -> CommentResponse:
        content = data.content.strip()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Nội dung bình luận không được để trống",
            )

        if data.parent_id:
            parent = await self.repo.get_by_id(data.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bình luận cha không tồn tại",
                )
            if parent.lesson_id != lesson_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bình luận cha không thuộc bài học này",
                )

        comment = Comment(
            lesson_id=lesson_id,
            user_id=user_id,
            parent_id=data.parent_id,
            content=content,
        )
        saved = await self.repo.create(comment)
        return CommentResponse(
            id=saved.id,
            lesson_id=saved.lesson_id,
            user_id=saved.user_id,
            parent_id=saved.parent_id,
            content=saved.content,
            created_at=saved.created_at,
            replies=[],
        )

    async def delete_comment(self, comment_id: UUID, user_id: UUID, roles: list[str]) -> None:
        comment = await self.repo.get_by_id(comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bình luận không tồn tại",
            )

        is_owner = str(comment.user_id) == str(user_id)
        normalized_roles = [r.lower() for r in roles]
        is_admin = "admin" in normalized_roles or "editor" in normalized_roles

        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Không có quyền xóa bình luận này",
            )

        await self.repo.delete(comment)
