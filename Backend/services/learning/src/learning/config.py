from functools import lru_cache

from pbl6_common.config import BaseServiceSettings


class LearningSettings(BaseServiceSettings):
    """Learning service reads the same env vars as every service, no extras."""


@lru_cache
def get_settings() -> LearningSettings:
    """Lazy, cached singleton — importing this module must never require env
    vars to be set (e.g. `from learning.config import LearningSettings` for a
    type hint in a unit test). Only actually reading settings does."""
    return LearningSettings()  # type: ignore[call-arg]
