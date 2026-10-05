import time
import typing
import uuid

import cloudinary
import cloudinary.uploader
import cloudinary.utils
from content.config import get_settings
from content.models.media_asset import MediaAsset, MediaKind
from content.repositories.lesson_repository import LessonRepository
from content.repositories.media_repository import MediaRepository
from content.schemas.media import MediaCreateRequest, PresignedUrlResponse
from pbl6_common.errors import AppError, NotFoundError


class MediaError(AppError):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class MediaService:
    def __init__(
        self,
        media_repo: MediaRepository,
        lesson_repo: LessonRepository,
    ):
        self.media_repo = media_repo
        self.lesson_repo = lesson_repo
        self.settings = get_settings()

        # Initialize Cloudinary config
        cloudinary.config(
            cloud_name=self.settings.cloudinary_cloud_name,
            api_key=self.settings.cloudinary_api_key,
            api_secret=self.settings.cloudinary_api_secret,
        )

    async def generate_presigned_url(self, req: MediaCreateRequest) -> PresignedUrlResponse:
        # Validate lesson exists
        lesson = await self.lesson_repo.get_by_id(req.lesson_id)
        if not lesson:
            raise NotFoundError("Bài học không tồn tại")

        file_uuid = uuid.uuid4().hex[:8]
        # Keep s3_key as a column name but store cloudinary public_id
        folder = f"lessons/{req.lesson_id}"
        public_id = f"{file_uuid}-{req.filename.rsplit('.', 1)[0]}"
        full_public_id = f"{folder}/{public_id}"

        # Cloudinary CDN url prediction
        # For simplicity, we just use the API to get URL later, but for prediction:
        ext = req.filename.split('.')[-1]
        cdn_url = f"https://res.cloudinary.com/{self.settings.cloudinary_cloud_name}/raw/upload/{full_public_id}.{ext}"
        if req.kind == MediaKind.IMAGE:
            cdn_url = f"https://res.cloudinary.com/{self.settings.cloudinary_cloud_name}/image/upload/{full_public_id}.{ext}"
        elif req.kind == MediaKind.AUDIO:
            cdn_url = f"https://res.cloudinary.com/{self.settings.cloudinary_cloud_name}/video/upload/{full_public_id}.{ext}"

        # Content restrictions
        max_size = 10 * 1024 * 1024  # 10 MB cap from backend.md
        if req.bytes > max_size:
            raise MediaError("FILE_TOO_LARGE", "File exceeds 10MB limit", 400)

        content_type = req.content_type
        if req.kind == MediaKind.AUDIO and not content_type.startswith("audio/"):
            raise MediaError("INVALID_CONTENT_TYPE", "Audio file required", 400)
        if req.kind == MediaKind.IMAGE and not content_type.startswith("image/"):
            raise MediaError("INVALID_CONTENT_TYPE", "Image file required", 400)

        # Generate Cloudinary upload signature
        timestamp = int(time.time())
        params_to_sign = {
            "timestamp": timestamp,
            "folder": folder,
            "public_id": public_id,
        }

        signature = cloudinary.utils.api_sign_request(
            params_to_sign, self.settings.cloudinary_api_secret
        )

        resource_type = "auto"
        if req.kind == MediaKind.IMAGE:
            resource_type = "image"
        elif req.kind == MediaKind.AUDIO:
            resource_type = "video"

        url = f"https://api.cloudinary.com/v1_1/{self.settings.cloudinary_cloud_name}/{resource_type}/upload"
        fields = {
            "api_key": self.settings.cloudinary_api_key,
            "timestamp": str(timestamp),
            "signature": signature,
            "folder": folder,
            "public_id": public_id,
        }

        # Save to database, mapping public_id to s3_key column for compatibility
        asset = MediaAsset(
            lesson_id=req.lesson_id,
            kind=req.kind,
            s3_key=full_public_id,
            cdn_url=cdn_url,
            bytes=req.bytes,
        )
        asset = await self.media_repo.create(asset)

        return PresignedUrlResponse(
            url=url,
            fields=fields,
            media_asset_id=typing.cast(uuid.UUID, asset.id),
            cdn_url=cdn_url,
        )

    async def delete_media(self, media_id: uuid.UUID) -> None:
        asset = await self.media_repo.get(media_id)
        if not asset:
            raise NotFoundError("Không tìm thấy file media")

        # Delete from Cloudinary
        try:
            resource_type = "image" if asset.kind == MediaKind.IMAGE else "video"
            cloudinary.uploader.destroy(typing.cast(str, asset.s3_key), resource_type=resource_type)
        except Exception:
            # We log but continue to delete from DB to avoid orphaned DB records
            pass

        await self.media_repo.delete(asset)

    async def get_media_by_lesson(self, lesson_id: uuid.UUID) -> list[MediaAsset]:
        return await self.media_repo.get_by_lesson(lesson_id)
