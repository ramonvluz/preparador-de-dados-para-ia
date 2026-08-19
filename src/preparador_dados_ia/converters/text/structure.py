from __future__ import annotations

import re
from dataclasses import dataclass

from markdown_it import MarkdownIt

from preparador_dados_ia.contracts.text import TextHeading, TextSection

ATX_HEADING = re.compile(r"^\s*(#{1,6})\s+(.+?)\s*#*\s*$")
SETEXT_UNDERLINE = re.compile(r"^\s*(={3,}|-{3,})\s*$")
NUMBERED_HEADING = re.compile(r"^\s*(\d+(?:\.\d+)*\.)\s+(.+?)\s*$")


@dataclass(frozen=True, slots=True)
class TextStructure:
    title: str | None
    headings: tuple[TextHeading, ...]
    sections: tuple[TextSection, ...]


def analyze_text_structure(content: str, *, markdown: bool) -> TextStructure:
    headings = _markdown_headings(content) if markdown else _plain_text_headings(content)
    sections = _sections_from_headings(content, headings)
    return TextStructure(
        title=headings[0].text if headings else None,
        headings=tuple(headings),
        sections=tuple(sections),
    )


def _markdown_headings(content: str) -> list[TextHeading]:
    tokens = MarkdownIt("commonmark").parse(content)
    headings: list[TextHeading] = []
    for index, token in enumerate(tokens):
        if token.type != "heading_open" or token.map is None:
            continue
        level = int(token.tag.removeprefix("h"))
        inline = tokens[index + 1] if index + 1 < len(tokens) else None
        text = inline.content.strip() if inline is not None and inline.type == "inline" else ""
        headings.append(TextHeading(level=level, text=text, line_number=token.map[0] + 1))
    return headings


def _plain_text_headings(content: str) -> list[TextHeading]:
    lines = content.splitlines()
    headings: list[TextHeading] = []
    consumed_lines: set[int] = set()
    for index, line in enumerate(lines):
        line_number = index + 1
        if line_number in consumed_lines or not line.strip():
            continue

        atx = ATX_HEADING.match(line)
        if atx:
            headings.append(
                TextHeading(level=len(atx.group(1)), text=atx.group(2), line_number=line_number)
            )
            continue

        if index + 1 < len(lines) and (underline := SETEXT_UNDERLINE.match(lines[index + 1])):
            level = 1 if underline.group(1).startswith("=") else 2
            headings.append(TextHeading(level=level, text=line.strip(), line_number=line_number))
            consumed_lines.add(line_number + 1)
            continue

        numbered = NUMBERED_HEADING.match(line)
        if numbered:
            numbering = numbered.group(1).rstrip(".)")
            level = min(numbering.count(".") + 1, 6)
            headings.append(TextHeading(level=level, text=line.strip(), line_number=line_number))
            continue

        stripped = line.strip()
        previous_blank = index == 0 or not lines[index - 1].strip()
        next_blank = index == len(lines) - 1 or not lines[index + 1].strip()
        if (
            previous_blank
            and next_blank
            and 3 <= len(stripped) <= 100
            and len(stripped.split()) <= 12
            and any(character.isalpha() for character in stripped)
            and stripped == stripped.upper()
            and not stripped.endswith((".", "!", "?", ":", ";"))
        ):
            headings.append(TextHeading(level=1, text=stripped, line_number=line_number))
    return headings


def _sections_from_headings(
    content: str,
    headings: list[TextHeading],
) -> list[TextSection]:
    lines = content.splitlines()
    if not lines:
        return []
    if not headings:
        return [
            TextSection(
                title=None,
                level=None,
                content=content.strip(),
                start_line=1,
                end_line=len(lines),
            )
        ]

    sections: list[TextSection] = []
    first_line = headings[0].line_number
    preamble = "\n".join(lines[: first_line - 1]).strip()
    if preamble:
        sections.append(
            TextSection(
                title=None,
                level=None,
                content=preamble,
                start_line=1,
                end_line=first_line - 1,
            )
        )

    for index, heading in enumerate(headings):
        end_line = headings[index + 1].line_number - 1 if index + 1 < len(headings) else len(lines)
        content_start = heading.line_number + 1
        if content_start <= len(lines) and SETEXT_UNDERLINE.match(lines[content_start - 1]):
            content_start += 1
        section_content = "\n".join(lines[content_start - 1 : end_line]).strip()
        sections.append(
            TextSection(
                title=heading.text,
                level=heading.level,
                content=section_content,
                start_line=heading.line_number,
                end_line=end_line,
            )
        )
    return sections
