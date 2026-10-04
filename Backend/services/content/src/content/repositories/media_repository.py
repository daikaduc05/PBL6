import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from content.models.media_asset import MediaAsset


class MediaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, asset: MediaAsset) -> MediaAsset:
        self.db.add(asset)
        await self.db.commit()
        await self.db.refresh(asset)
        return asset

    async def get(self, media_id: uuid.UUID) -> MediaAsset | None:
        stmt = select(MediaAsset).where(MediaAsset.id == media_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_lesson(self, lesson_id: uuid.UUID) -> list[MediaAsset]:
        stmt = select(MediaAsset).where(MediaAsset.lesson_id == lesson_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, asset: MediaAsset) -> None:
        await self.db.delete(asset)
        await self.db.commit()
