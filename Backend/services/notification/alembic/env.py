import asyncio
from logging.config import fileConfig

from alembic import context
from notification.config import get_settings
from notification.models import Message, NotificationSetting, ProcessedEvent  # noqa: F401
from pbl6_common.db import Base, make_engine
from sqlalchemy.ext.asyncio import AsyncEngine

settings = get_settings()
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Each service keeps its own alembic_version table inside its own schema, so
# the five services sharing one Supabase database never collide.
VERSION_TABLE_SCHEMA = "notification"


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=VERSION_TABLE_SCHEMA,
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    # Alembic creates its version table before running any revision, so the
    # schema has to exist first. On Supabase 00_schemas.sql already made it and
    # this is a no-op; on a fresh database (CI, a test container) it is what
    # lets `upgrade head` work with no raw SQL applied beforehand.
    connection.exec_driver_sql(f"CREATE SCHEMA IF NOT EXISTS {VERSION_TABLE_SCHEMA}")

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_schema=VERSION_TABLE_SCHEMA,
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine: AsyncEngine = make_engine(settings.database_url)
    # engine.begin(), not engine.connect(): SQLAlchemy 2.0 rolls back an
    # uncommitted connection on exit, so with connect() the whole upgrade is
    # silently discarded and `alembic upgrade head` reports success against an
    # unchanged database.
    async with engine.begin() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
