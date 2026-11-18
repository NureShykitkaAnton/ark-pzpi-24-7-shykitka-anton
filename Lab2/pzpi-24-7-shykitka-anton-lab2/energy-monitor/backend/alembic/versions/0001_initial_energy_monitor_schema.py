"""Initial schema for EnergyMonitor database (10 tables).

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-05 23:55:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Створює всі 12 таблиць бази даних системи контролю енергоспоживання будинку."""
    # 1. Таблиця користувачів (users)
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=50), nullable=True),
        sa.Column("last_name", sa.String(length=50), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "Active", "Banned", name="userstatus", native_enum=False, length=20
            ),
            server_default="Active",
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Enum("User", "Admin", name="userrole", native_enum=False, length=20),
            server_default="User",
            nullable=False,
        ),
        sa.Column(
            "subscription_tier",
            sa.Enum(
                "Free", "Pro", name="subscriptiontier", native_enum=False, length=20
            ),
            server_default="Free",
            nullable=False,
        ),
        sa.Column("locale", sa.String(length=10), server_default="uk", nullable=False),
        sa.Column(
            "timezone",
            sa.String(length=64),
            server_default="Europe/Kyiv",
            nullable=False,
        ),
        sa.Column(
            "measurement_system",
            sa.Enum(
                "Metric",
                "Imperial",
                name="measurementsystem",
                native_enum=False,
                length=20,
            ),
            server_default="Metric",
            nullable=False,
        ),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    # 2. Таблиця refresh-токенів (refresh_tokens)
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_refresh_tokens_id"), "refresh_tokens", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_refresh_tokens_token_hash"),
        "refresh_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False
    )

    # 3. Таблиця тарифів (tariffs)
    op.create_table(
        "tariffs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "currency", sa.String(length=10), server_default="UAH", nullable=False
        ),
        sa.Column(
            "day_rate_per_kwh", sa.Numeric(precision=10, scale=4), nullable=False
        ),
        sa.Column("night_multiplier", sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column("night_start_time", sa.Time(), nullable=False),
        sa.Column("night_end_time", sa.Time(), nullable=False),
        sa.Column("is_two_zone", sa.Boolean(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("day_rate_per_kwh > 0", name="ck_tariffs_positive_day_rate"),
        sa.CheckConstraint(
            "night_multiplier > 0 AND night_multiplier <= 1",
            name="ck_tariffs_valid_night_multiplier",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tariffs_id"), "tariffs", ["id"], unique=False)
    op.create_index(op.f("ix_tariffs_user_id"), "tariffs", ["user_id"], unique=False)

    # 4. Таблиця ліній живлення та датчиків ESP32 (power_lines)
    op.create_table(
        "power_lines",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("tariff_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("device_uid", sa.String(length=64), nullable=False),
        sa.Column("device_token_hash", sa.String(length=64), nullable=False),
        sa.Column("nominal_voltage", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column(
            "max_current_limit", sa.Numeric(precision=8, scale=2), nullable=False
        ),
        sa.Column(
            "spike_threshold_watts", sa.Numeric(precision=10, scale=2), nullable=False
        ),
        sa.Column("sampling_interval_sec", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "nominal_voltage > 0", name="ck_power_lines_positive_voltage"
        ),
        sa.CheckConstraint(
            "max_current_limit > 0", name="ck_power_lines_positive_current"
        ),
        sa.CheckConstraint(
            "spike_threshold_watts > 0", name="ck_power_lines_positive_spike"
        ),
        sa.CheckConstraint(
            "sampling_interval_sec >= 1", name="ck_power_lines_valid_interval"
        ),
        sa.ForeignKeyConstraint(["tariff_id"], ["tariffs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_power_lines_device_token_hash"),
        "power_lines",
        ["device_token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_power_lines_device_uid"), "power_lines", ["device_uid"], unique=True
    )
    op.create_index(op.f("ix_power_lines_id"), "power_lines", ["id"], unique=False)
    op.create_index(
        op.f("ix_power_lines_tariff_id"), "power_lines", ["tariff_id"], unique=False
    )
    op.create_index(
        op.f("ix_power_lines_user_id"), "power_lines", ["user_id"], unique=False
    )

    # 5. Таблиця місячних бюджетів (budgets)
    op.create_table(
        "budgets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("power_line_id", sa.Uuid(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("limit_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("consumed_kwh", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column(
            "accumulated_cost", sa.Numeric(precision=12, scale=2), nullable=False
        ),
        sa.Column("forecasted_cost", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "warn_threshold_pct", sa.Numeric(precision=5, scale=2), nullable=False
        ),
        sa.Column("warn_notified", sa.Boolean(), nullable=False),
        sa.Column("limit_notified", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("limit_amount > 0", name="ck_budgets_positive_limit"),
        sa.CheckConstraint("month BETWEEN 1 AND 12", name="ck_budgets_valid_month"),
        sa.CheckConstraint(
            "warn_threshold_pct > 0 AND warn_threshold_pct <= 100",
            name="ck_budgets_valid_warn_pct",
        ),
        sa.ForeignKeyConstraint(
            ["power_line_id"], ["power_lines.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "power_line_id", "year", "month", name="uq_budgets_line_year_month"
        ),
    )
    op.create_index(op.f("ix_budgets_id"), "budgets", ["id"], unique=False)
    op.create_index(
        op.f("ix_budgets_power_line_id"), "budgets", ["power_line_id"], unique=False
    )

    # 6. Таблиця часових рядів телеметрії (telemetry_readings)
    op.create_table(
        "telemetry_readings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("power_line_id", sa.Uuid(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("voltage_rms", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("current_rms", sa.Numeric(precision=8, scale=3), nullable=False),
        sa.Column("active_power", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("power_factor", sa.Numeric(precision=5, scale=3), nullable=False),
        sa.Column(
            "energy_delta_kwh", sa.Numeric(precision=12, scale=6), nullable=False
        ),
        sa.Column(
            "tariff_zone", sa.String(length=16), server_default="DAY", nullable=False
        ),
        sa.Column("cost_delta", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("is_buffered", sa.Boolean(), nullable=False),
        sa.Column("is_interpolated", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["power_line_id"], ["power_lines.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_telemetry_readings_id"), "telemetry_readings", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_telemetry_readings_power_line_id"),
        "telemetry_readings",
        ["power_line_id"],
        unique=False,
    )
    op.create_index(
        "ix_telemetry_line_recorded_at",
        "telemetry_readings",
        ["power_line_id", "recorded_at"],
        unique=False,
    )

    # 7. Таблиця аномальних подій (anomaly_events)
    op.create_table(
        "anomaly_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("power_line_id", sa.Uuid(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "anomaly_type",
            sa.Enum(
                "POWER_SPIKE",
                "OVERLOAD",
                "TIME_GAP",
                "VOLTAGE_OUT_OF_RANGE",
                "SENSOR_OFFLINE",
                name="anomalytype",
                native_enum=False,
                length=40,
            ),
            nullable=False,
        ),
        sa.Column(
            "delta_power_watts", sa.Numeric(precision=10, scale=2), nullable=False
        ),
        sa.Column(
            "peak_power_watts", sa.Numeric(precision=10, scale=2), nullable=False
        ),
        sa.Column("user_appliance_label", sa.String(length=120), nullable=True),
        sa.Column("llm_explanation", sa.Text(), nullable=True),
        sa.Column("is_acknowledged", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["power_line_id"], ["power_lines.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_anomaly_events_id"), "anomaly_events", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_anomaly_events_power_line_id"),
        "anomaly_events",
        ["power_line_id"],
        unique=False,
    )
    op.create_index(
        "ix_anomaly_events_line_detected_at",
        "anomaly_events",
        ["power_line_id", "detected_at"],
        unique=False,
    )

    # 8. Таблиця профілів навантаження (load_profiles)
    op.create_table(
        "load_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("power_line_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("readings_payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["power_line_id"], ["power_lines.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_load_profiles_id"), "load_profiles", ["id"], unique=False)
    op.create_index(
        op.f("ix_load_profiles_power_line_id"),
        "load_profiles",
        ["power_line_id"],
        unique=False,
    )

    # 9. Таблиця журналу аудиту (audit_logs)
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.String(length=80), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False
    )
    op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)
    op.create_index(
        op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False
    )

    # 10. Таблиця резервних копій бази даних (system_backups)
    op.create_table(
        "system_backups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="COMPLETED",
            nullable=False,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("filename"),
    )
    op.create_index(
        op.f("ix_system_backups_created_by_id"),
        "system_backups",
        ["created_by_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_system_backups_id"), "system_backups", ["id"], unique=False
    )

    # 11. Таблиця push-токенів мобільних пристроїв (push_tokens)
    op.create_table(
        "push_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "platform",
            sa.Enum(
                "ANDROID",
                "IOS",
                "WEB",
                name="pushplatform",
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("device_token", sa.String(length=512), nullable=False),
        sa.Column("device_name", sa.String(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_push_tokens_device_token"),
        "push_tokens",
        ["device_token"],
        unique=True,
    )
    op.create_index(op.f("ix_push_tokens_id"), "push_tokens", ["id"], unique=False)
    op.create_index(
        op.f("ix_push_tokens_user_id"), "push_tokens", ["user_id"], unique=False
    )

    # 12. Таблиця системних і push-сповіщень (notifications)
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("power_line_id", sa.Uuid(), nullable=True),
        sa.Column(
            "notification_type",
            sa.Enum(
                "BUDGET_WARN_80",
                "BUDGET_LIMIT_100",
                "POWER_SPIKE",
                "OVERLOAD",
                "SENSOR_OFFLINE",
                name="notificationtype",
                native_enum=False,
                length=40,
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["power_line_id"], ["power_lines.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_id"), "notifications", ["id"], unique=False)
    op.create_index(
        op.f("ix_notifications_power_line_id"),
        "notifications",
        ["power_line_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notifications_user_id"), "notifications", ["user_id"], unique=False
    )
    op.create_index(
        "ix_notifications_user_created_at",
        "notifications",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Відкат міграції: видаляє створені таблиці у зворотному порядку залежностей."""
    op.drop_table("notifications")
    op.drop_table("push_tokens")
    op.drop_table("system_backups")
    op.drop_table("audit_logs")
    op.drop_table("load_profiles")
    op.drop_table("anomaly_events")
    op.drop_table("telemetry_readings")
    op.drop_table("budgets")
    op.drop_table("power_lines")
    op.drop_table("tariffs")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
