from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path


def slugify_filename(path: Path) -> str:
    decomposed = unicodedata.normalize("NFKD", path.stem)
    ascii_name = decomposed.encode("ascii", errors="ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_name).strip("_")
    return slug[:100] or "conversao"


def automatic_output_dir(input_path: Path, output_root: Path, started_at: datetime) -> Path:
    timestamp = started_at.astimezone().strftime("%Y%m%d_%H%M%S")
    base_name = f"{slugify_filename(input_path)}__{timestamp}"
    candidate = output_root / base_name
    suffix = 2
    while candidate.exists():
        candidate = output_root / f"{base_name}__{suffix:02d}"
        suffix += 1
    return candidate


def find_possible_duplicates(output_root: Path, input_path: Path) -> list[Path]:
    if not output_root.is_dir():
        return []
    source_stat = input_path.stat()
    duplicates: list[Path] = []
    for report_path in output_root.glob("*/relatorio_conversao.json"):
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            sources = report.get("sources")
            source = sources[0] if isinstance(sources, list) and sources else {}
            if (
                isinstance(source, dict)
                and source.get("size_bytes") == source_stat.st_size
                and source.get("file_name") == input_path.name
            ):
                duplicates.append(report_path.parent)
        except (OSError, ValueError, TypeError, KeyError):
            continue
    return duplicates
