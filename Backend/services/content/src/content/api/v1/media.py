import uuid

from fastapi import APIRouter, Depends, status
from pbl6_common.deps import require_role

from content.deps import get_media_service
from content.schemas.media import MediaAssetResponse, MediaCreateRequest, PresignedUrlResponse
from content.services.media_service import MediaService

router = APIRouter(prefix="/media", tags=["Media"])


@router.post(
    "/presigned-url",
    response_model=PresignedUrlResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "editor"))],
)
async def generate_presigned_url(
    data: MediaCreateRequest,
    service: MediaService = Depends(get_media_service),
):
    return await service.generate_presigned_url(data)


@router.delete(
    "/{media_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin", "editor"))],
)
async def delete_media(
    media_id: uuid.UUID,
    service: MediaService = Depends(get_media_service),
):
    await service.delete_media(media_id)


@router.get(
    "/lessons/{lesson_id}",
    response_model=list[MediaAssetResponse],
)
async def list_lesson_media(
    lesson_id: uuid.UUID,
    service: MediaService = Depends(get_media_service),
):
    return await service.get_media_by_lesson(lesson_id)
