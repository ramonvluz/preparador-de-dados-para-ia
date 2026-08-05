from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

ProgressStage = Literal["preparing", "converting", "writing", "completed", "cancelled"]


@dataclass(frozen=True, slots=True)
class ConversionProgress:
    stage: ProgressStage
    current: int
    total: int | None = None


ProgressCallback = Callable[[ConversionProgress], None]
