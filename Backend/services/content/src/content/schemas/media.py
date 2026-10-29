import uuid

from content.models.media_asset import MediaKind
from pydantic import BaseModel, ConfigDict


class MediaCreateRequest(BaseModel):
    lesson_id: uuid.UUID
    kind: MediaKind
    filename: str
    content_type: str
    bytes: int


class PresignedUrlResponse(BaseModel):
    url: str
    fields: dict[str, str]
    media_asset_id: uuid.UUID
    cdn_url: str


class MediaAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lesson_id: uuid.UUID
    kind: MediaKind
    s3_key: str
    cdn_url: str
    bytes: int
