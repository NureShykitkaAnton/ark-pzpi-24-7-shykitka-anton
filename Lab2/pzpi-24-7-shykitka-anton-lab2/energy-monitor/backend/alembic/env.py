"""Конфігурація асинхронного середовища міграцій бази даних Alembic."""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.core.config import settings
from app.core.models import Base

# Імпорт усіх ORM-моделей для їх реєстрації у метаданих Base.metadata
from app.modules.admin.models import AuditLog, SystemBackup  # noqa: F401
from app.modules.anomalies.models import AnomalyEvent  # noqa: F401
from app.modules.auth.models import RefreshToken  # noqa: F401
from app.modules.budgets.models import Budget  # noqa: F401
from app.modules.lines.models import PowerLine  # noqa: F401
from app.modules.notifications.models import Notification, PushToken  # noqa: F401
from app.modules.tariffs.models import Tariff  # noqa: F401
from app.modules.telemetry.models import LoadProfile, TelemetryReading  # noqa: F401
from app.modules.users.models import User  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Виконує генерацію SQL-міграцій в автономному (offline) режимі."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Запускає міграції в онлайн-режимі через асинхронний рушій SQLAlchemy."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Точка входу онлайн-міграцій."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
