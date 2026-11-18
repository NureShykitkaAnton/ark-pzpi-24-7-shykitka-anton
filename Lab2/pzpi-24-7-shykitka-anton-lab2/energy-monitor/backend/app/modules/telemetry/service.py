"""Сервіс обробки телеметрії, контролю часових пропусків, розрахунку вартості та програвання профілів."""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.anomalies.enums import AnomalyType
from app.modules.anomalies.repository import AnomalyRepository
from app.modules.budgets.service import BudgetService
from app.modules.lines.models import PowerLine
from app.modules.lines.repository import PowerLineRepository
from app.modules.lines.service import PowerLineService
from app.modules.tariffs.repository import TariffRepository
from app.modules.tariffs.service import TariffService
from app.modules.telemetry.models import LoadProfile, TelemetryReading
from app.modules.telemetry.repository import LoadProfileRepository, TelemetryRepository
from app.modules.telemetry.schemas import (
    LoadProfileCreate,
    LoadProfileReplayResult,
    TelemetryIngestRequest,
    TelemetryIngestResponse,
    TelemetryReadingRead,
    TelemetrySummaryResponse,
)


class TelemetryService:
    """Сервіс централізованої математичної обробки та архівування телеметрії."""

    def __init__(
        self,
        telemetry_repo: TelemetryRepository,
        profile_repo: LoadProfileRepository,
        line_repo: PowerLineRepository,
        line_service: PowerLineService,
        tariff_repo: TariffRepository,
        anomaly_repo: AnomalyRepository,
        budget_service: BudgetService,
    ) -> None:
        self.telemetry_repo = telemetry_repo
        self.profile_repo = profile_repo
        self.line_repo = line_repo
        self.line_service = line_service
        self.tariff_repo = tariff_repo
        self.anomaly_repo = anomaly_repo
        self.budget_service = budget_service

    async def ingest_samples(
        self,
        data: TelemetryIngestRequest,
        iot_line: PowerLine | None = None,
        user_id: uuid.UUID | None = None,
    ) -> TelemetryIngestResponse:
        """Приймає пакет відліків, контролює неперервність часових міток, фіксує аномалії та оновлює бюджет."""
        if iot_line is not None:
            line = iot_line
        elif data.power_line_id is not None and user_id is not None:
            line = await self.line_service.get_user_line(data.power_line_id, user_id)
        else:
            raise BadRequestException(
                "Either X-Device-Token header or power_line_id with user authentication is required"
            )

        sorted_samples = sorted(data.samples, key=lambda s: s.recorded_at)
        previous_reading = await self.telemetry_repo.get_latest_for_line(line.id)

        created_readings: list[TelemetryReading] = []
        interpolated_count = 0
        anomalies_count = 0

        expected_step = max(1, line.sampling_interval_sec)

        for sample in sorted_samples:
            sample_ts = (
                sample.recorded_at
                if sample.recorded_at.tzinfo is not None
                else sample.recorded_at.replace(tzinfo=UTC)
            )
            active_power = (
                sample.active_power
                if sample.active_power is not None
                else (
                    sample.voltage_rms * sample.current_rms * sample.power_factor
                ).quantize(Decimal("0.01"))
            )

            # 1. Контроль часових пропусків (якщо розрив перевищує 3 очікуваних інтервали)
            if previous_reading is not None:
                prev_ts = (
                    previous_reading.recorded_at
                    if previous_reading.recorded_at.tzinfo is not None
                    else previous_reading.recorded_at.replace(tzinfo=UTC)
                )
                gap_seconds = (sample_ts - prev_ts).total_seconds()
                if gap_seconds > expected_step * 3 and gap_seconds <= 3600:
                    midpoint_ts = prev_ts + timedelta(seconds=gap_seconds / 2)
                    interp_v = (
                        (previous_reading.voltage_rms + sample.voltage_rms) / Decimal(2)
                    ).quantize(Decimal("0.01"))
                    interp_i = (
                        (previous_reading.current_rms + sample.current_rms) / Decimal(2)
                    ).quantize(Decimal("0.001"))
                    interp_p = (
                        (previous_reading.active_power + active_power) / Decimal(2)
                    ).quantize(Decimal("0.01"))
                    interp_dt_hours = Decimal(str(gap_seconds / 2)) / Decimal(3600)
                    interp_kwh = (
                        (interp_p / Decimal(1000)) * interp_dt_hours
                    ).quantize(Decimal("0.000001"))
                    zone, rate = TariffService.resolve_zone_and_rate(
                        line.tariff, midpoint_ts.timetz().replace(tzinfo=None)
                    )
                    interp_cost = (interp_kwh * rate).quantize(Decimal("0.0001"))

                    interp_reading = await self.telemetry_repo.create(
                        power_line_id=line.id,
                        recorded_at=midpoint_ts,
                        voltage_rms=interp_v,
                        current_rms=interp_i,
                        active_power=interp_p,
                        power_factor=sample.power_factor,
                        energy_delta_kwh=interp_kwh,
                        tariff_zone=zone,
                        cost_delta=interp_cost,
                        is_buffered=False,
                        is_interpolated=True,
                    )
                    created_readings.append(interp_reading)
                    interpolated_count += 1

                    await self.anomaly_repo.create(
                        power_line_id=line.id,
                        detected_at=midpoint_ts,
                        anomaly_type=AnomalyType.TIME_GAP,
                        delta_power_watts=abs(
                            active_power - previous_reading.active_power
                        ),
                        peak_power_watts=max(
                            active_power, previous_reading.active_power
                        ),
                    )
                    anomalies_count += 1
                    await self.budget_service.register_consumption(
                        line.id, midpoint_ts, interp_kwh, interp_cost
                    )
                    previous_reading = interp_reading

            # 2. Обчислення інтервалу часу та спожитої енергії
            if previous_reading is not None:
                prev_ts = (
                    previous_reading.recorded_at
                    if previous_reading.recorded_at.tzinfo is not None
                    else previous_reading.recorded_at.replace(tzinfo=UTC)
                )
                dt_seconds = max(
                    1.0,
                    min(
                        (sample_ts - prev_ts).total_seconds(), float(expected_step * 4)
                    ),
                )
            else:
                dt_seconds = float(expected_step)

            dt_hours = Decimal(str(dt_seconds)) / Decimal(3600)
            energy_delta_kwh = ((active_power / Decimal(1000)) * dt_hours).quantize(
                Decimal("0.000001")
            )

            zone, rate = TariffService.resolve_zone_and_rate(
                line.tariff, sample_ts.timetz().replace(tzinfo=None)
            )
            cost_delta = (energy_delta_kwh * rate).quantize(Decimal("0.0001"))

            # 3. Детектування аномальних стрибків потужності (ΔP > P_threshold) та перевантажень
            if previous_reading is not None:
                delta_p = active_power - previous_reading.active_power
                if delta_p >= line.spike_threshold_watts:
                    await self.anomaly_repo.create(
                        power_line_id=line.id,
                        detected_at=sample_ts,
                        anomaly_type=AnomalyType.POWER_SPIKE,
                        delta_power_watts=delta_p.quantize(Decimal("0.01")),
                        peak_power_watts=active_power,
                    )
                    anomalies_count += 1
            elif active_power >= line.spike_threshold_watts:
                await self.anomaly_repo.create(
                    power_line_id=line.id,
                    detected_at=sample_ts,
                    anomaly_type=AnomalyType.POWER_SPIKE,
                    delta_power_watts=active_power,
                    peak_power_watts=active_power,
                )
                anomalies_count += 1

            if sample.current_rms > line.max_current_limit:
                await self.anomaly_repo.create(
                    power_line_id=line.id,
                    detected_at=sample_ts,
                    anomaly_type=AnomalyType.OVERLOAD,
                    delta_power_watts=active_power,
                    peak_power_watts=active_power,
                )
                anomalies_count += 1

            reading = await self.telemetry_repo.create(
                power_line_id=line.id,
                recorded_at=sample_ts,
                voltage_rms=sample.voltage_rms,
                current_rms=sample.current_rms,
                active_power=active_power,
                power_factor=sample.power_factor,
                energy_delta_kwh=energy_delta_kwh,
                tariff_zone=zone,
                cost_delta=cost_delta,
                is_buffered=sample.is_buffered,
                is_interpolated=False,
            )
            created_readings.append(reading)
            previous_reading = reading

            await self.budget_service.register_consumption(
                line.id, sample_ts, energy_delta_kwh, cost_delta
            )

        if created_readings:
            await self.line_repo.update(
                line, last_seen_at=created_readings[-1].recorded_at
            )

        return TelemetryIngestResponse(
            ingested_count=len(created_readings) - interpolated_count,
            interpolated_gaps_count=interpolated_count,
            anomalies_detected_count=anomalies_count,
            readings=[TelemetryReadingRead.model_validate(r) for r in created_readings],
        )

    async def list_readings(
        self,
        user_id: uuid.UUID,
        power_line_id: uuid.UUID,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 500,
    ) -> Sequence[TelemetryReading]:
        """Повертає часовий ряд вимірювань для обраної лінії користувача."""
        await self.line_service.get_user_line(power_line_id, user_id)
        return await self.telemetry_repo.get_range_for_line(
            power_line_id=power_line_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

    async def get_summary(
        self,
        user_id: uuid.UUID,
        power_line_id: uuid.UUID,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> TelemetrySummaryResponse:
        """Обчислює агреговану статистику споживання (день/ніч, піки, пропуски)."""
        await self.line_service.get_user_line(power_line_id, user_id)
        readings = await self.telemetry_repo.get_range_for_line(
            power_line_id=power_line_id,
            start_time=start_time,
            end_time=end_time,
            limit=5000,
        )
        if not readings:
            return TelemetrySummaryResponse(
                power_line_id=power_line_id,
                total_readings=0,
                interpolated_readings=0,
                buffered_readings=0,
                total_energy_kwh=Decimal("0.0000"),
                day_energy_kwh=Decimal("0.0000"),
                night_energy_kwh=Decimal("0.0000"),
                total_cost=Decimal("0.00"),
                avg_power_watts=Decimal("0.00"),
                peak_power_watts=Decimal("0.00"),
            )

        total_kwh = sum((r.energy_delta_kwh for r in readings), Decimal("0.000000"))
        day_kwh = sum(
            (r.energy_delta_kwh for r in readings if r.tariff_zone == "DAY"),
            Decimal("0.000000"),
        )
        night_kwh = sum(
            (r.energy_delta_kwh for r in readings if r.tariff_zone == "NIGHT"),
            Decimal("0.000000"),
        )
        total_cost = sum((r.cost_delta for r in readings), Decimal("0.0000"))
        avg_power = sum((r.active_power for r in readings), Decimal("0.00")) / Decimal(
            len(readings)
        )
        peak_power = max(r.active_power for r in readings)

        return TelemetrySummaryResponse(
            power_line_id=power_line_id,
            total_readings=len(readings),
            interpolated_readings=sum(1 for r in readings if r.is_interpolated),
            buffered_readings=sum(1 for r in readings if r.is_buffered),
            total_energy_kwh=total_kwh.quantize(Decimal("0.0001")),
            day_energy_kwh=day_kwh.quantize(Decimal("0.0001")),
            night_energy_kwh=night_kwh.quantize(Decimal("0.0001")),
            total_cost=total_cost.quantize(Decimal("0.01")),
            avg_power_watts=avg_power.quantize(Decimal("0.01")),
            peak_power_watts=peak_power.quantize(Decimal("0.01")),
        )

    async def create_profile(
        self, user_id: uuid.UUID, data: LoadProfileCreate
    ) -> LoadProfile:
        """Зберігає еталонний або історичний профіль навантаження у БД."""
        await self.line_service.get_user_line(data.power_line_id, user_id)
        return await self.profile_repo.create(**data.model_dump())

    async def list_profiles(
        self, user_id: uuid.UUID, power_line_id: uuid.UUID | None = None
    ) -> Sequence[LoadProfile]:
        """Повертає список збережених профілів навантаження."""
        return await self.profile_repo.get_by_user(
            user_id=user_id, power_line_id=power_line_id
        )

    async def replay_profile(
        self,
        profile_id: uuid.UUID,
        user_id: uuid.UUID,
        tariff_id: uuid.UUID | None = None,
    ) -> LoadProfileReplayResult:
        """Моделює витрати електроенергії шляхом повторного програвання збереженого профілю за обраним тарифом."""
        profile = await self.profile_repo.get_by_id(profile_id)
        if not profile:
            raise NotFoundException("Load profile not found")
        line = await self.line_service.get_user_line(profile.power_line_id, user_id)

        tariff = line.tariff
        if tariff_id is not None:
            tariff = await self.tariff_repo.get_by_id(tariff_id)
            if not tariff:
                raise NotFoundException("Tariff for replay simulation not found")

        total_kwh = Decimal("0.000000")
        day_kwh = Decimal("0.000000")
        night_kwh = Decimal("0.000000")
        total_cost = Decimal("0.0000")

        for item in profile.readings_payload:
            power_w = Decimal(str(item.get("active_power", 0)))
            duration_sec = Decimal(
                str(item.get("duration_sec", line.sampling_interval_sec))
            )
            hour_int = int(item.get("hour", 12))
            from datetime import time as dt_time

            sim_time = dt_time(hour=hour_int % 24, minute=0, second=0)
            zone, rate = TariffService.resolve_zone_and_rate(tariff, sim_time)
            kwh = (power_w / Decimal(1000)) * (duration_sec / Decimal(3600))
            total_kwh += kwh
            if zone == "NIGHT":
                night_kwh += kwh
            else:
                day_kwh += kwh
            total_cost += kwh * rate

        return LoadProfileReplayResult(
            profile_id=profile.id,
            profile_name=profile.name,
            simulated_samples=len(profile.readings_payload),
            total_energy_kwh=total_kwh.quantize(Decimal("0.0001")),
            day_energy_kwh=day_kwh.quantize(Decimal("0.0001")),
            night_energy_kwh=night_kwh.quantize(Decimal("0.0001")),
            simulated_total_cost=total_cost.quantize(Decimal("0.01")),
            currency=tariff.currency if tariff else "UAH",
        )
