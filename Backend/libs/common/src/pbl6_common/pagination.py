"""Shared pagination envelope (backend.md §7):

{ "items": [...], "total": 0, "page": 1, "size": 20 }
"""

from pydantic import BaseModel


class Paginated[T](BaseModel):
    items: list[T]
    total: int
    page: int
    size: int
