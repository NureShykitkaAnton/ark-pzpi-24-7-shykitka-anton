"""Комплексне функціональне тестування БД та REST API системи EnergyMonitor (ЛР №2)."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient) -> None:
    """Перевірка доступності сервера та з'єднання з БД."""
    resp = await async_client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["database"] == "connected"


@pytest.mark.asyncio
async def test_full_energy_monitor_workflow(async_client: AsyncClient) -> None:
    """Наскрізний тест: реєстрація -> тариф -> лінія ESP32 -> бюджет -> телеметрія -> аномалії -> LLM."""
    suffix = uuid.uuid4().hex[:8]
    # 1. Реєстрація користувача
    reg_resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": f"anton.shykitka.{suffix}@nure.ua",
            "password": "StrongPassword123!",
            "first_name": "Антон",
            "last_name": "Шикітка",
            "locale": "uk",
            "timezone": "Europe/Kyiv",
        },
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Створення двозонного тарифу «День/Ніч»
    tariff_resp = await async_client.post(
        "/api/v1/tariffs",
        headers=headers,
        json={
            "name": "Двозонний тариф (День/Ніч)",
            "currency": "UAH",
            "day_rate_per_kwh": "4.3200",
            "night_multiplier": "0.5000",
            "night_start_time": "23:00:00",
            "night_end_time": "07:00:00",
            "is_two_zone": True,
            "is_default": True,
        },
    )
    assert tariff_resp.status_code == 201
    tariff_id = tariff_resp.json()["id"]

    # 3. Створення лінії живлення та реєстрація датчика ESP32
    line_resp = await async_client.post(
        "/api/v1/lines",
        headers=headers,
        json={
            "name": "Головний ввід квартири",
            "description": "Щиток DIN-рейка, ESP32 + SCT-013",
            "device_uid": f"ESP32-{suffix.upper()}",
            "tariff_id": tariff_id,
            "nominal_voltage": "230.00",
            "max_current_limit": "25.00",
            "spike_threshold_watts": "800.00",
            "sampling_interval_sec": 5,
        },
    )
    assert line_resp.status_code == 201
    line_data = line_resp.json()
    line_id = line_data["id"]
    device_token = line_data["device_api_token"]
    assert device_token.startswith("em_iot_")

    # 4. Встановлення місячного бюджету на листопад 2026
    budget_resp = await async_client.post(
        "/api/v1/budgets",
        headers=headers,
        json={
            "power_line_id": line_id,
            "year": 2026,
            "month": 11,
            "limit_amount": "1500.00",
            "warn_threshold_pct": "80.00",
        },
    )
    assert budget_resp.status_code == 201
    budget_id = budget_resp.json()["id"]

    # 5. Відправка пакета телеметрії від ESP32 за X-Device-Token (включно зі стрибком потужності та пропуском часу)
    ingest_resp = await async_client.post(
        "/api/v1/telemetry/ingest",
        headers={"X-Device-Token": device_token},
        json={
            "samples": [
                {
                    "recorded_at": "2026-11-05T21:00:00Z",
                    "voltage_rms": "229.50",
                    "current_rms": "1.500",
                    "power_factor": "0.980",
                    "is_buffered": False,
                },
                {
                    "recorded_at": "2026-11-05T21:00:05Z",
                    "voltage_rms": "228.10",
                    "current_rms": "10.800",
                    "power_factor": "0.990",
                    "is_buffered": False,
                },
                {
                    "recorded_at": "2026-11-05T21:00:30Z",
                    "voltage_rms": "230.00",
                    "current_rms": "2.100",
                    "power_factor": "0.980",
                    "is_buffered": True,
                },
            ]
        },
    )
    assert ingest_resp.status_code == 201
    ingest_data = ingest_resp.json()
    assert ingest_data["ingested_count"] == 3
    assert ingest_data["interpolated_gaps_count"] == 1
    assert ingest_data["anomalies_detected_count"] >= 2

    # 6. Отримання агрегованої статистики споживання
    summary_resp = await async_client.get(
        "/api/v1/telemetry/summary",
        headers=headers,
        params={"power_line_id": line_id},
    )
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["total_readings"] == 4
    assert summary["interpolated_readings"] == 1
    assert summary["buffered_readings"] == 1

    # 7. Перевірка оновлення місячного бюджету
    budget_check = await async_client.get(
        f"/api/v1/budgets/{budget_id}", headers=headers
    )
    assert budget_check.status_code == 200
    assert float(budget_check.json()["consumed_kwh"]) > 0

    # 8. Перевірка зафіксованих аномалій, маркування приладу та генерація пояснення від LLM
    anom_resp = await async_client.get(
        "/api/v1/anomalies",
        headers=headers,
        params={"power_line_id": line_id},
    )
    assert anom_resp.status_code == 200
    anomalies = anom_resp.json()
    assert len(anomalies) >= 2
    spike_anomaly = next(a for a in anomalies if a["anomaly_type"] == "POWER_SPIKE")
    anomaly_id = spike_anomaly["id"]

    label_resp = await async_client.patch(
        f"/api/v1/anomalies/{anomaly_id}/label",
        headers=headers,
        json={"user_appliance_label": "Бойлер 2.2 кВт", "is_acknowledged": True},
    )
    assert label_resp.status_code == 200
    assert label_resp.json()["user_appliance_label"] == "Бойлер 2.2 кВт"

    explain_resp = await async_client.post(
        f"/api/v1/anomalies/{anomaly_id}/explain",
        headers=headers,
        json={"locale": "uk"},
    )
    assert explain_resp.status_code == 200
    assert "ΔP =" in explain_resp.json()["llm_explanation"]

    # 9. Збереження та повторне програвання профілю навантаження
    profile_resp = await async_client.post(
        "/api/v1/telemetry/profiles",
        headers=headers,
        json={
            "power_line_id": line_id,
            "name": "Вечірній та нічний профіль бойлера",
            "readings_payload": [
                {"hour": 19, "active_power": 2000, "duration_sec": 3600},
                {"hour": 2, "active_power": 2000, "duration_sec": 3600},
            ],
        },
    )
    assert profile_resp.status_code == 201
    profile_id = profile_resp.json()["id"]

    replay_resp = await async_client.post(
        f"/api/v1/telemetry/profiles/{profile_id}/replay",
        headers=headers,
        json={"tariff_id": tariff_id},
    )
    assert replay_resp.status_code == 200
    replay_data = replay_resp.json()
    assert float(replay_data["total_energy_kwh"]) == 4.0
    assert float(replay_data["day_energy_kwh"]) == 2.0
    assert float(replay_data["night_energy_kwh"]) == 2.0
    # 2 кВт·год * 4.32 + 2 кВт·год * 2.16 = 8.64 + 4.32 = 12.96 грн
    assert float(replay_data["simulated_total_cost"]) == 12.96

    # 10. Реєстрація push-токена мобільного клієнта (FCM/APNs) та перевірка сповіщень
    push_resp = await async_client.post(
        "/api/v1/notifications/push-tokens",
        headers=headers,
        json={
            "platform": "ANDROID",
            "device_token": f"fcm_test_token_{suffix}_1234567890abcdef",
            "device_name": "Pixel 8 Pro",
        },
    )
    assert push_resp.status_code == 201
    assert push_resp.json()["platform"] == "ANDROID"

    notif_resp = await async_client.get("/api/v1/notifications", headers=headers)
    assert notif_resp.status_code == 200

    # 10. Експорт конфігурації з перевіркою контрольної суми SHA-256
    export_resp = await async_client.get("/api/v1/admin/export", headers=headers)
    assert export_resp.status_code == 200
    assert len(export_resp.json()["checksum_sha256"]) == 64
