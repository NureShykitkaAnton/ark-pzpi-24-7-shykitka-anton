"""Спеціалізовані типи даних та валідатори для схем Pydantic."""

import uuid
from typing import Annotated

from pydantic import AfterValidator


def validate_uuid7(v: uuid.UUID) -> uuid.UUID:
    """Перевіряє, що переданий UUID відповідає версії 7 (або допустимому UUID)."""
    if v.version is not None and v.version not in (4, 7):
        raise ValueError(f"UUID must be version 7 (or 4), got version {v.version}")
    return v


UUID7 = Annotated[uuid.UUID, AfterValidator(validate_uuid7)]
