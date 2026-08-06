from pathlib import Path

import pytest

from limebh_preparador.converters.text.reader import decode_text_bytes, read_text_source
from limebh_preparador.core.cancellation import CancellationToken, ConversionCancelled


def test_utf8_bom_is_removed_without_warning() -> None:
    decoded = decode_text_bytes("\ufeffAção local".encode("utf-8"))

    assert decoded.content == "Ação local"
    assert decoded.encoding == "utf-8"
    assert decoded.warnings == ()


def test_ambiguous_portuguese_single_byte_prefers_windows_1252() -> None:
    content = (
        "Relatório de contratação e manutenção. Ação, órgão, informações e seção administrativa. "
    ) * 10

    decoded = decode_text_bytes(content.encode("cp1252"))

    assert decoded.content == content
    assert decoded.encoding == "cp1252"
    assert "encoding_ambiguous_windows_1252_preferred" in decoded.warnings


def test_reader_honours_cancellation(tmp_path: Path) -> None:
    source = tmp_path / "cancelado.txt"
    source.write_text("conteúdo", encoding="utf-8")
    token = CancellationToken()
    token.cancel()

    with pytest.raises(ConversionCancelled):
        read_text_source(source, token)
