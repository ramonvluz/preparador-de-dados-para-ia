from __future__ import annotations

import html
import re
import unicodedata
from collections import Counter
from html.parser import HTMLParser
from typing import ClassVar


class _HTMLTextExtractor(HTMLParser):
    BLOCK_TAGS: ClassVar[set[str]] = {
        "br",
        "p",
        "div",
        "li",
        "tr",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        value = html.unescape("".join(self.parts))
        value = re.sub(r"[ \t]+", " ", value)
        value = re.sub(r"\n\s*\n\s*\n+", "\n\n", value)
        return value.strip()


def html_to_text(value: str) -> str:
    parser = _HTMLTextExtractor()
    try:
        parser.feed(value)
        parser.close()
        return parser.text()
    except Exception:
        return re.sub(r"<[^>]+>", " ", value).strip()


_REMOVED_INVISIBLE = {
    "\u00ad",
    "\u200b",
    "\u200c",
    "\u200d",
    "\u200e",
    "\u200f",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u2060",
    "\u2066",
    "\u2067",
    "\u2068",
    "\u2069",
    "\ufeff",
}


class UnicodeSanitizer:
    """Normaliza ruído Unicode mantendo acentos, emojis e pontuação válida."""

    def __init__(self) -> None:
        self.changes: Counter[str] = Counter()

    def clean(self, value: str) -> str:
        output: list[str] = []
        for character in value:
            codepoint = ord(character)
            if character == "\u00a0":
                output.append(" ")
                self.changes["no_break_space_replaced"] += 1
            elif character in {"\u2028", "\u2029"}:
                output.append("\n")
                self.changes["unicode_line_separator_replaced"] += 1
            elif character in _REMOVED_INVISIBLE:
                self.changes[f"removed_U+{codepoint:04X}"] += 1
            elif 0x80 <= codepoint <= 0x9F:
                try:
                    replacement = bytes([codepoint]).decode("windows-1252")
                except UnicodeDecodeError:
                    replacement = ""
                output.append(replacement)
                self.changes["windows_1252_control_repaired"] += 1
            elif unicodedata.category(character) == "Cc" and character not in "\n\r\t":
                self.changes[f"control_removed_U+{codepoint:04X}"] += 1
            else:
                output.append(character)
        return unicodedata.normalize("NFC", "".join(output))

    def report(self) -> dict[str, object]:
        return {
            "total_changes": sum(self.changes.values()),
            "by_rule": dict(sorted(self.changes.items())),
        }


def sanitize_record(value: object, sanitizer: UnicodeSanitizer) -> object:
    if isinstance(value, str):
        return sanitizer.clean(value)
    if isinstance(value, list):
        return [sanitize_record(item, sanitizer) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_record(item, sanitizer) for key, item in value.items()}
    return value
