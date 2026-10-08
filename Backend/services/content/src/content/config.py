from functools import lru_cache

from pbl6_common.config import BaseServiceSettings


class ContentSettings(BaseServiceSettings):
    """Content service reads the same env vars as every service, plus AWS configs."""

    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""


@lru_cache
def get_settings() -> ContentSettings:
    """Lazy, cached singleton — importing this module must never require env
    vars to be set. Only actually reading settings does."""
    return ContentSettings()  # type: ignore[call-arg]
