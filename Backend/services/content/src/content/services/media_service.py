import typing
import uuid

import boto3
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

        # Initialize boto3 S3 client
        self.s3_client = boto3.client(
            "s3",
            region_name=self.settings.aws_region,
        )

    async def generate_presigned_url(self, req: MediaCreateRequest) -> PresignedUrlResponse:
        # Validate lesson exists
        lesson = await self.lesson_repo.get_by_id(req.lesson_id)
        if not lesson:
            raise NotFoundError("Bài học không tồn tại")

        # S3 key format: lessons/{lesson_id}/{uuid}-{filename}
        file_uuid = uuid.uuid4().hex[:8]
        s3_key = f"lessons/{req.lesson_id}/{file_uuid}-{req.filename}"
        cdn_url = f"{self.settings.cdn_base_url.rstrip('/')}/{s3_key}"

        # Content restrictions
        max_size = 10 * 1024 * 1024  # 10 MB cap from backend.md
        if req.bytes > max_size:
            raise MediaError("FILE_TOO_LARGE", "File exceeds 10MB limit", 400)

        content_type = req.content_type
        if req.kind == MediaKind.AUDIO and not content_type.startswith("audio/"):
            raise MediaError("INVALID_CONTENT_TYPE", "Audio file required", 400)
        if req.kind == MediaKind.IMAGE and not content_type.startswith("image/"):
            raise MediaError("INVALID_CONTENT_TYPE", "Image file required", 400)

        # Generate presigned POST with conditions
        conditions = [
            {"acl": "public-read"},
            ["content-length-range", 0, max_size],
            ["eq", "$Content-Type", content_type],
            {"Cache-Control": "max-age=31536000, immutable"},
        ]

        fields = {
            "acl": "public-read",
            "Content-Type": content_type,
            "Cache-Control": "max-age=31536000, immutable",
        }

        try:
            presigned = self.s3_client.generate_presigned_post(
                Bucket=self.settings.s3_bucket,
                Key=s3_key,
                Fields=fields,
                Conditions=conditions,
                ExpiresIn=3600,
            )
        except Exception as e:
            raise MediaError("S3_ERROR", f"Failed to generate S3 url: {str(e)}", 500) from e

        # Save to database
        asset = MediaAsset(
            lesson_id=req.lesson_id, kind=req.kind, s3_key=s3_key, cdn_url=cdn_url, bytes=req.bytes
        )
        asset = await self.media_repo.create(asset)

        return PresignedUrlResponse(
            url=presigned["url"],
            fields=presigned["fields"],
            media_asset_id=typing.cast(uuid.UUID, asset.id),
            cdn_url=cdn_url,
        )

    async def delete_media(self, media_id: uuid.UUID) -> None:
        asset = await self.media_repo.get(media_id)
        if not asset:
            raise NotFoundError("Không tìm thấy file media")

        # Delete from S3
        try:
            self.s3_client.delete_object(
                Bucket=self.settings.s3_bucket, Key=typing.cast(str, asset.s3_key)
            )
        except Exception:
            # We log but continue to delete from DB to avoid orphaned DB records
            pass

        await self.media_repo.delete(asset)

    async def get_media_by_lesson(self, lesson_id: uuid.UUID) -> list[MediaAsset]:
        return await self.media_repo.get_by_lesson(lesson_id)
