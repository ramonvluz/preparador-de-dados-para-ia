from __future__ import annotations

import codecs
from dataclasses import dataclass
from pathlib import Path

from charset_normalizer import CharsetMatch, from_bytes

from preparador_dados_ia.core.cancellation import CancellationToken

READ_CHUNK_BYTES = 1024 * 1024


@dataclass(frozen=True, slots=True)
class DecodedText:
    content: str
    encoding: str
    warnings: tuple[str, ...] = ()


def read_text_source(path: Path, cancellation_token: CancellationToken) -> DecodedText:
    """Lê a fonte em blocos e detecta a codificação sem alterar o arquivo."""

    raw = bytearray()
    with path.open("rb") as source:
        while chunk := source.read(READ_CHUNK_BYTES):
            cancellation_token.raise_if_cancelled()
            raw.extend(chunk)
    cancellation_token.raise_if_cancelled()
    return decode_text_bytes(bytes(raw))


def decode_text_bytes(raw: bytes) -> DecodedText:
    bom_result = _decode_bom(raw)
    if bom_result is not None:
        return bom_result

    try:
        return DecodedText(raw.decode("utf-8"), "utf-8")
    except UnicodeDecodeError:
        pass

    matches = from_bytes(raw)
    selected = matches.best()
    if selected is None:
        return DecodedText(
            raw.decode("utf-8", errors="replace"),
            "utf-8",
            ("encoding_detection_failed_utf8_replacement",),
        )

    warnings: list[str] = []
    windows_1252 = next(
        (match for match in matches if _normalized_encoding(match) == "cp1252"),
        None,
    )
    if windows_1252 is not None and _is_ambiguous_single_byte(selected):
        if _normalized_encoding(selected) != "cp1252":
            warnings.append("encoding_ambiguous_windows_1252_preferred")
        selected = windows_1252

    content = str(selected)
    encoding = _normalized_encoding(selected)
    if selected.chaos >= 0.2:
        warnings.append("encoding_low_confidence")
    if "\ufffd" in content:
        warnings.append("encoding_replacement_characters_present")
    return DecodedText(content, encoding, tuple(warnings))


def _decode_bom(raw: bytes) -> DecodedText | None:
    bom_decoders = (
        (codecs.BOM_UTF32_LE, "utf-32", "utf-32-le"),
        (codecs.BOM_UTF32_BE, "utf-32", "utf-32-be"),
        (codecs.BOM_UTF8, "utf-8-sig", "utf-8"),
        (codecs.BOM_UTF16_LE, "utf-16", "utf-16-le"),
        (codecs.BOM_UTF16_BE, "utf-16", "utf-16-be"),
    )
    for marker, decoder, label in bom_decoders:
        if raw.startswith(marker):
            return DecodedText(raw.decode(decoder), label)
    return None


def _normalized_encoding(match: CharsetMatch) -> str:
    return str(match.encoding or "unknown").lower().replace("_", "-")


def _is_ambiguous_single_byte(match: CharsetMatch) -> bool:
    encoding = _normalized_encoding(match)
    return encoding.startswith(("cp12", "iso8859", "latin", "mac-", "hp-"))
