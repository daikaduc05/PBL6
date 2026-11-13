import asyncio

from content.config import get_settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def main():
    engine = create_async_engine(get_settings().database_url)
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS content.media_assets CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS content.lessons CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS content.categories CASCADE;"))
        await conn.execute(text("DROP TYPE IF EXISTS content.lesson_access_enum CASCADE;"))
        await conn.execute(text("DROP TYPE IF EXISTS content.lesson_level_enum CASCADE;"))
        await conn.execute(text("DROP TYPE IF EXISTS content.lesson_status_enum CASCADE;"))
        await conn.execute(text("DROP TYPE IF EXISTS content.media_kind_enum CASCADE;"))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
