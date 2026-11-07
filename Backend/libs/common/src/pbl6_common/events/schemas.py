"""Event envelope shared by every publisher/consumer (backend.md §6).

Every service that puts a message on `pbl6.events` wraps it in this exact
shape, and every consumer reads this shape regardless of event_type —
`data` is the only part that varies. `event_id` is the dedup key consumers
key their idempotency table on (see notification service's
`processed_events`, keyed on this field).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class EventEnvelope(BaseModel):
    event_id: uuid.UUID
    event_type: str
    version: int = 1
    occurred_at: datetime
    producer: str
    data: dict[str, Any]
