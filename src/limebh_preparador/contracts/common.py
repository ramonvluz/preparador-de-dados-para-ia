from __future__ import annotations

import hashlib
from collections.abc import Mapping
from datetime import UTC, datetime

SCHEMA_VERSION = "1.0"


def build_document_record(
    *,
    record_type: str,
    record_prefix: str,
    source_file: str,
    source_file_type: str,
    source_size_bytes: int,
    data: Mapping[str, object],
    converted_at: datetime | None = None,
    warnings: list[str] | None = None,
    unicode_cleaned: bool = True,
    logical_key: str = "document",
    processing: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Monta o envelope comum dos documentos sem expor o caminho da fonte."""

    _validate_source_file_name(source_file)
    if not record_type or not record_prefix or not source_file_type:
        raise ValueError("Tipo de registro, prefixo e tipo de fonte são obrigatórios")
    if source_size_bytes < 0:
        raise ValueError("O tamanho da fonte não pode ser negativo")
    if not logical_key:
        raise ValueError("A chave lógica do registro é obrigatória")

    timestamp = converted_at or datetime.now(UTC)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)

    processing_extras = dict(processing or {})
    reserved_processing = {"converted_at", "unicode_cleaned", "warnings"}
    if reserved_processing.intersection(processing_extras):
        raise ValueError("Campos comuns de processamento não podem ser sobrescritos")

    fingerprint = "\0".join([record_type, source_file, str(source_size_bytes), logical_key]).encode(
        "utf-8", errors="replace"
    )
    digest = hashlib.sha256(fingerprint).hexdigest()[:24]

    processing_data: dict[str, object] = {
        "converted_at": timestamp.isoformat(),
        "unicode_cleaned": unicode_cleaned,
        "warnings": list(warnings or []),
    }
    processing_data.update(processing_extras)

    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": record_type,
        "record_id": f"{record_prefix}_{digest}",
        "source": {
            "file_name": source_file,
            "file_type": source_file_type,
            "size_bytes": source_size_bytes,
        },
        "data": dict(data),
        "processing": processing_data,
    }


def _validate_source_file_name(source_file: str) -> None:
    if not source_file or source_file in {".", ".."} or "/" in source_file or "\\" in source_file:
        raise ValueError("source_file deve conter somente o nome do arquivo")
