"""Database queries only — never raises an HTTP exception (backend.md §3
layering rule: api -> services -> repositories -> models)."""

from __future__ import annotations

import uuid

from account.models.user import User
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(func.lower(User.email) == email.lower())
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def create(
        self, *, email: str, password_hash: str, full_name: str, role: str = "CUSTOMER"
    ) -> User:
        user = User(email=email, password_hash=password_hash, full_name=full_name, role=role)
        self._session.add(user)
        await self._session.flush()
        return user

    async def save(self, user: User) -> None:
        """Persists in-place mutations on an already-loaded User (the caller
        mutates attributes on the instance from get_by_id/get_by_email)."""
        await self._session.flush()

    async def list_by_role(
        self,
        *,
        role: str,
        page: int,
        size: int,
        status: str | None = None,
        q: str | None = None,
    ) -> tuple[list[User], int]:
        """Excludes soft-deleted rows. Shared by the student (T23) and editor
        (T24) admin screens — each only ever passes its own role, so neither
        can see or touch the other's accounts.

        T25: `status` filters exactly; `q` matches full_name or email,
        case-insensitive, substring (ILIKE)."""
        conditions = [User.role == role, User.deleted_at.is_(None)]
        if status is not None:
            conditions.append(User.status == status)
        if q:
            pattern = f"%{q.lower()}%"
            conditions.append(
                or_(func.lower(User.full_name).like(pattern), func.lower(User.email).like(pattern))
            )

        base = select(User).where(*conditions)

        total = await self._session.scalar(select(func.count()).select_from(base.subquery()))

        stmt = base.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total or 0
