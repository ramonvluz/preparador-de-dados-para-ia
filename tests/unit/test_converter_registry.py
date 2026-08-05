from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest

from limebh_preparador.converters import (
    ConversionContext,
    ConverterRegistrationError,
    ConverterRegistry,
    RecordConverter,
    UnsupportedSourceFormat,
)
from limebh_preparador.core.cancellation import CancellationToken


class FakeConverter:
    def __init__(
        self,
        converter_id: str,
        record_type: str,
        supported_extensions: frozenset[str],
    ) -> None:
        self.converter_id = converter_id
        self.record_type = record_type
        self.supported_extensions = supported_extensions

    def convert(self, context: ConversionContext) -> Iterator[dict[str, object]]:
        context.cancellation_token.raise_if_cancelled()
        yield {"record_type": self.record_type, "source": context.source.name}


def test_registry_resolves_case_insensitive_extensions_and_streams_records() -> None:
    converter = FakeConverter(
        converter_id="plain_text",
        record_type="text_document",
        supported_extensions=frozenset({"TXT", ".md"}),
    )
    registry = ConverterRegistry()
    registry.register(converter)
    context = ConversionContext(
        source=Path("ORIENTACOES.MD"),
        source_size_bytes=10,
        converted_at=datetime(2026, 8, 5, 17, 0, tzinfo=UTC),
        cancellation_token=CancellationToken(),
    )

    selected = registry.resolve(context.source)

    assert isinstance(selected, RecordConverter)
    assert selected is converter
    assert list(selected.convert(context)) == [
        {"record_type": "text_document", "source": "ORIENTACOES.MD"}
    ]
    assert registry.supported_extensions == (".md", ".txt")
    assert registry.get("plain_text") is converter


def test_conflicting_registration_is_rejected_atomically() -> None:
    registry = ConverterRegistry()
    registry.register(FakeConverter("text", "text_document", frozenset({".txt"})))

    with pytest.raises(ConverterRegistrationError, match="já registrada"):
        registry.register(FakeConverter("other", "other_document", frozenset({".txt", ".pdf"})))

    assert registry.supported_extensions == (".txt",)
    with pytest.raises(UnsupportedSourceFormat):
        registry.resolve(Path("arquivo.pdf"))


def test_registry_reports_unsupported_or_extensionless_sources() -> None:
    registry = ConverterRegistry()

    with pytest.raises(UnsupportedSourceFormat, match=".docx"):
        registry.resolve(Path("arquivo.docx"))
    with pytest.raises(UnsupportedSourceFormat, match="sem extensão"):
        registry.resolve(Path("LEIA_ME"))


def test_conversion_context_requires_aware_timestamp() -> None:
    with pytest.raises(ValueError, match="fuso horário"):
        ConversionContext(
            source=Path("arquivo.txt"),
            source_size_bytes=10,
            converted_at=datetime(2026, 8, 5, 17, 0),
            cancellation_token=CancellationToken(),
        )
