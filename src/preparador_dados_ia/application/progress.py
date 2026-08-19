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


def notify_progress(
    callback: ProgressCallback | None,
    stage: ProgressStage,
    current: int,
    total: int | None = None,
) -> None:
    if callback is not None:
        callback(ConversionProgress(stage=stage, current=current, total=total))
