"""HTTP-based access to data owned by Account Service and Learning Service.

Replaces the legacy cross-schema SQL queries (`SELECT ... FROM account.users`
and `SELECT ... FROM learning.histories`) with proper internal HTTP API calls:
- `GET {account_service_url}/internal/account/active-users`
- `GET {account_service_url}/internal/account/users/{id}`
- `GET {learning_service_url}/internal/learning/last-activity?since=...`

Preserves strict Database-per-Service and Service Autonomy principles.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from notification.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ActiveUser:
    id: uuid.UUID
    email: str
    full_name: str


class ExternalReader:
    def __init__(
        self,
        session: AsyncSession | None = None,
        *,
        account_base_url: str | None = None,
        learning_base_url: str | None = None,
        internal_secret: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ):
        # `session` is accepted for backward-compatible constructor signature
        # in existing wiring, but no cross-schema SQL is ever executed on it.
        self._session = session
        try:
            settings = get_settings()
            default_account_url = settings.account_service_url
            default_learning_url = settings.learning_service_url
            default_secret = settings.internal_api_secret
        except Exception:
            default_account_url = "http://localhost:8001"
            default_learning_url = "http://localhost:8003"
            default_secret = "pbl6-internal-gateway-secret"

        self._account_url = (account_base_url or default_account_url).rstrip("/")
        self._learning_url = (learning_base_url or default_learning_url).rstrip("/")
        self._internal_secret = internal_secret or default_secret
        self._client = http_client

    def _headers(self) -> dict[str, str]:
        return {"X-Internal-Secret": self._internal_secret}

    async def _get_json(self, url: str, *, params: dict[str, Any] | None = None) -> Any:
        if self._client is not None:
            resp = await self._client.get(url, params=params, headers=self._headers(), timeout=5.0)
            resp.raise_for_status()
            return resp.json()

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    async def active_users(self) -> list[ActiveUser]:
        """Fetches active users from Account Service via HTTP:
        GET /internal/account/active-users
        """
        url = f"{self._account_url}/internal/account/active-users"
        data = await self._get_json(url)
        return [
            ActiveUser(
                id=uuid.UUID(str(item["id"])),
                email=item["email"],
                full_name=item["full_name"],
            )
            for item in data
        ]

    async def user(self, user_id: uuid.UUID) -> ActiveUser | None:
        """Fetches a single user from Account Service via HTTP:
        GET /internal/account/users/{id}
        """
        url = f"{self._account_url}/internal/account/users/{user_id}"
        try:
            item = await self._get_json(url)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise
        return ActiveUser(
            id=uuid.UUID(str(item["id"])),
            email=item["email"],
            full_name=item["full_name"],
        )

    async def user_ids_studied_since(self, since: datetime) -> set[uuid.UUID]:
        """Fetches users who studied since `since` from Learning Service via HTTP:
        GET /internal/learning/last-activity?since=...
        """
        url = f"{self._learning_url}/internal/learning/last-activity"
        data = await self._get_json(url, params={"since": since.isoformat()})
        items = data.get("items", []) if isinstance(data, dict) else []
        return {uuid.UUID(str(item["user_id"])) for item in items}
