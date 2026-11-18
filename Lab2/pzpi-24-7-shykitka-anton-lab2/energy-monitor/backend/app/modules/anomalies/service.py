"""Сервіс аналізу аномалій, маркування приладів та формування пояснень на базі LLM."""

import uuid
from collections.abc import Sequence
from decimal import Decimal

from app.core.exceptions import NotFoundException
from app.modules.anomalies.enums import AnomalyType
from app.modules.anomalies.models import AnomalyEvent
from app.modules.anomalies.repository import AnomalyRepository
from app.modules.anomalies.schemas import AnomalyLabelUpdate
from app.modules.lines.service import PowerLineService


class AnomalyService:
    """Сервіс управління аномаліями та інтелектуального пояснення динаміки навантаження."""

    def __init__(self, repo: AnomalyRepository, line_service: PowerLineService) -> None:
        self.repo = repo
        self.line_service = line_service

    async def list_anomalies(
        self,
        user_id: uuid.UUID,
        power_line_id: uuid.UUID | None = None,
        anomaly_type: AnomalyType | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AnomalyEvent]:
        """Повертає список аномальних подій користувача."""
        return await self.repo.get_by_user(
            user_id=user_id,
            power_line_id=power_line_id,
            anomaly_type=anomaly_type,
            skip=skip,
            limit=limit,
        )

    async def get_user_anomaly(
        self, anomaly_id: uuid.UUID, user_id: uuid.UUID
    ) -> AnomalyEvent:
        """Отримує аномалію за UUID і перевіряє право доступу до лінії."""
        anomaly = await self.repo.get_by_id(anomaly_id)
        if not anomaly:
            raise NotFoundException("Anomaly event not found")
        await self.line_service.get_user_line(anomaly.power_line_id, user_id)
        return anomaly

    async def label_appliance(
        self, anomaly_id: uuid.UUID, user_id: uuid.UUID, data: AnomalyLabelUpdate
    ) -> AnomalyEvent:
        """Зберігає позначку побутового приладу, вказану користувачем."""
        anomaly = await self.get_user_anomaly(anomaly_id, user_id)
        return await self.repo.update(
            anomaly,
            user_appliance_label=data.user_appliance_label.strip(),
            is_acknowledged=data.is_acknowledged,
        )

    async def generate_llm_explanation(
        self, anomaly_id: uuid.UUID, user_id: uuid.UUID, locale: str = "uk"
    ) -> AnomalyEvent:
        """Формує контекстне текстове пояснення стрибка навантаження з дотриманням аналітичних обмежень."""
        anomaly = await self.get_user_anomaly(anomaly_id, user_id)
        delta_w = anomaly.delta_power_watts
        peak_w = anomaly.peak_power_watts
        ts_str = anomaly.detected_at.strftime("%Y-%m-%d %H:%M:%S UTC")

        if locale == "en":
            hypothesis = self._infer_hypothesis_en(delta_w)
            explanation = (
                f"At {ts_str}, an event of type '{anomaly.anomaly_type.value}' was recorded "
                f"with a power jump ΔP = {delta_w} W (peak load: {peak_w} W). "
                f"Probabilistic hypothesis: {hypothesis}. "
                "Analytical limitation: single-point ammeter/wattmeter jump analysis provides "
                "probabilistic hypotheses only and does not guarantee exact appliance identification."
            )
        else:
            hypothesis = self._infer_hypothesis_uk(delta_w)
            explanation = (
                f"О {ts_str} зафіксовано подію типу «{anomaly.anomaly_type.value}» "
                f"зі стрибком активної потужності ΔP = {delta_w} Вт (пікове навантаження: {peak_w} Вт). "
                f"Ймовірнісна гіпотеза: {hypothesis}. "
                "Аналітичне застереження: система формує ймовірнісні припущення за часовим рядом "
                "і не гарантує однозначної ідентифікації конкретного електроприладу виключно за амперметрією одиничного стрибка."
            )

        return await self.repo.update(anomaly, llm_explanation=explanation)

    @staticmethod
    def _infer_hypothesis_uk(delta_w: Decimal) -> str:
        if delta_w >= Decimal(1800):
            return "увімкнення потужного резистивного нагрівача (електрочайник, бойлер, пральна машина у режимі нагріву або духова шафа)"
        if delta_w >= Decimal(800):
            return "запуск середньопотужного побутового споживача (мікрохвильова піч, пилосос, кондиціонер або обігрівач)"
        return "зміна режиму навантаження або часовий розрив у потоці телеметрії"

    @staticmethod
    def _infer_hypothesis_en(delta_w: Decimal) -> str:
        if delta_w >= Decimal(1800):
            return "activation of a high-power resistive heating appliance (electric kettle, water heater, washing machine heating cycle, or oven)"
        if delta_w >= Decimal(800):
            return "startup of a medium-power household load (microwave, vacuum cleaner, air conditioner, or space heater)"
        return "load state transition or telemetry time-series discontinuity"
