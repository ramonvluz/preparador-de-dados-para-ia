from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path

from preparador_dados_ia.core.partitioning import (
    PartitionLimits,
    estimate_tokens,
    json_text,
)
from preparador_dados_ia.outputs.atomic import atomic_write_text


class OutputFormat(StrEnum):
    JSON = "json"
    JSONL = "jsonl"


@dataclass(frozen=True, slots=True)
class PartInfo:
    file: str
    messages: int
    estimated_tokens: int
    size_bytes: int
    first_date: str | None
    last_date: str | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class PartWriter:
    """Agrupa registros sem ultrapassar os limites configurados."""

    def __init__(
        self,
        output_dir: Path,
        limits: PartitionLimits,
        output_format: OutputFormat,
        filename_prefix: str = "emails",
    ) -> None:
        wrapper_bytes = 2 if output_format is OutputFormat.JSON else 1
        if limits.max_bytes <= wrapper_bytes or limits.max_tokens <= 1:
            raise ValueError("Os limites são pequenos demais para produzir uma parte válida.")
        self.output_dir = output_dir
        self.limits = limits
        self.output_format = output_format
        if re.fullmatch(r"[a-z0-9_]+", filename_prefix) is None:
            raise ValueError("O prefixo das partes contém caracteres inválidos")
        self.filename_prefix = filename_prefix
        self._records: list[tuple[dict[str, object], str]] = []
        self._current_bytes = 2 if output_format is OutputFormat.JSON else 0
        self.parts: list[PartInfo] = []

    @property
    def single_record_limits(self) -> PartitionLimits:
        wrapper_bytes = 2 if self.output_format is OutputFormat.JSON else 1
        return PartitionLimits(
            max_bytes=self.limits.max_bytes - wrapper_bytes,
            max_tokens=self.limits.max_tokens - 1,
        )

    def _projected_bytes(self, serialized: str) -> int:
        record_bytes = len(serialized.encode("utf-8"))
        if self.output_format is OutputFormat.JSON:
            return self._current_bytes + record_bytes + (1 if self._records else 0)
        return self._current_bytes + record_bytes + 1

    def add(self, record: dict[str, object]) -> None:
        serialized = json_text(record)
        projected_bytes = self._projected_bytes(serialized)
        projected_tokens = max(1, (projected_bytes + 1) // 2)
        if self._records and (
            projected_bytes > self.limits.max_bytes or projected_tokens > self.limits.max_tokens
        ):
            self.flush()
            projected_bytes = self._projected_bytes(serialized)

        self._records.append((record, serialized))
        self._current_bytes = projected_bytes

    def flush(self) -> None:
        if not self._records:
            return
        suffix = self.output_format.value
        filename = f"{self.filename_prefix}_parte_{len(self.parts) + 1:04d}.{suffix}"
        path = self.output_dir / filename
        if self.output_format is OutputFormat.JSON:
            content = "[" + ",".join(item[1] for item in self._records) + "]"
        else:
            content = "".join(item[1] + "\n" for item in self._records)
        atomic_write_text(path, content)

        dates = sorted(
            str(record["data"]["date"])
            for record, _ in self._records
            if isinstance(record.get("data"), dict) and record["data"].get("date") is not None
        )
        size_bytes = path.stat().st_size
        self.parts.append(
            PartInfo(
                file=filename,
                messages=len(self._records),
                estimated_tokens=estimate_tokens(content),
                size_bytes=size_bytes,
                first_date=dates[0] if dates else None,
                last_date=dates[-1] if dates else None,
            )
        )
        self._records = []
        self._current_bytes = 2 if self.output_format is OutputFormat.JSON else 0
