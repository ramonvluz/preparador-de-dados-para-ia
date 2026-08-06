from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from limebh_preparador.application.progress import ProgressCallback
from limebh_preparador.core.cancellation import CancellationToken
from limebh_preparador.core.cleaning import UnicodeSanitizer


@dataclass(frozen=True, slots=True)
class ConversionContext:
    """Dados comuns entregues a qualquer conversor registrado."""

    source: Path
    source_size_bytes: int
    converted_at: datetime
    cancellation_token: CancellationToken
    progress_callback: ProgressCallback | None = None
    unicode_sanitizer: UnicodeSanitizer | None = None
    options: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.source_size_bytes < 0:
            raise ValueError("O tamanho da fonte não pode ser negativo")
        if self.converted_at.tzinfo is None:
            raise ValueError("A data da conversão deve conter fuso horário")


@runtime_checkable
class RecordConverter(Protocol):
    """Interface de conversão incremental entre uma fonte e registros versionados."""

    converter_id: str
    record_type: str
    supported_extensions: frozenset[str]

    def convert(self, context: ConversionContext) -> Iterator[dict[str, object]]:
        """Produz registros aos poucos e respeita o cancelamento do contexto."""
        ...
