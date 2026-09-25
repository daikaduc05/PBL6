"""Service-local dependency wiring: this service's own DB engine/session."""

from __future__ import annotations

from pbl6_common.db import make_engine, make_get_db, make_session_factory

from content.config import get_settings

settings = get_settings()
engine = make_engine(settings.database_url)
_session_factory = make_session_factory(engine)
get_db = make_get_db(_session_factory)
