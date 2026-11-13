"""Read-only access to schemas this service does not own.

Every cross-schema query in the codebase lives here (project_spec §0.4), under
four rules:

1. ``SELECT`` only — writing to another context's schema is never acceptable.
2. No cross-schema ``JOIN`` — each schema is queried separately and the results
   are combined in Python, so every query maps onto one future API call.
3. All of it in this one file, nowhere else.
4. When Hà's internal HTTP endpoints exist, only these method bodies change.

Possible at all only because the five services share one Supabase database
(Backend/db/README.md). It is a deliberate debt with an exit, not a shortcut.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class ActiveUser:
    id: uuid.UUID
    email: str
    full_name: str


class ExternalReader:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def active_users(self) -> list[ActiveUser]:
        """Owner: Long (account service).

        Future equivalent: GET /internal/account/active-users
        """
        rows = await self._session.execute(
            text(
                "select id, email, full_name "
                "from account.users "
                "where status = 'ACTIVE' and deleted_at is null"
            )
        )
        return [ActiveUser(id=r.id, email=r.email, full_name=r.full_name) for r in rows]

    async def user(self, user_id: uuid.UUID) -> ActiveUser | None:
        """Owner: Long (account service). One user, for the event consumer —
        a payment.succeeded payload carries only the user_id, not the email
        the confirmation should be sent to.

        Future equivalent: GET /internal/account/users/{id}

        No status filter, unlike active_users: a payment receipt or a lock
        notice must reach the account it concerns even if that account is not
        ACTIVE right now (account.locked is in fact *always* about one).
        """
        row = (
            await self._session.execute(
                text(
                    "select id, email, full_name "
                    "from account.users "
                    "where id = :id and deleted_at is null"
                ),
                {"id": user_id},
            )
        ).first()
        if row is None:
            return None
        return ActiveUser(id=row.id, email=row.email, full_name=row.full_name)

    async def user_ids_studied_since(self, since: datetime) -> set[uuid.UUID]:
        """Owner: Hà (learning service).

        Future equivalent: GET /internal/learning/last-activity

        Caveat worth knowing: ``learning.histories`` keeps one row per
        (user, lesson) holding the best score. Whether ``completed_at`` moves
        on every submission or only on an improvement is still unconfirmed with
        Hà (notif_spec §5.7). If it only moves on an improvement, someone who
        redoes a lesson and scores lower still counts as "has not studied".
        """
        rows = await self._session.execute(
            text("select distinct user_id from learning.histories where completed_at >= :since"),
            {"since": since},
        )
        return {r.user_id for r in rows}
