from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from limebh_preparador.application.conversion import (
    ConversionSettings,
    DestinationProfile,
)


class UiProfile(StrEnum):
    PLATFORM = "Plataforma de IA"
    API = "API / File Search"

    @property
    def destination_profile(self) -> DestinationProfile:
        if self is UiProfile.API:
            return DestinationProfile.API
        return DestinationProfile.PLATFORM


@dataclass(frozen=True, slots=True)
class FormatRecommendation:
    format_name: str
    explanation: str


def recommendation_for(profile: UiProfile) -> FormatRecommendation:
    if profile is UiProfile.API:
        return FormatRecommendation(
            format_name="JSONL particionado",
            explanation=(
                "Um registro por linha, com metadados preservados para pipelines técnicos "
                "e busca semântica."
            ),
        )
    return FormatRecommendation(
        format_name="JSON particionado",
        explanation=(
            "Partes independentes e numeradas, adequadas para envio manual a uma plataforma de IA."
        ),
    )


@dataclass(frozen=True, slots=True)
class DesktopConversionRequest:
    source: Path
    output_root: Path
    profile: UiProfile = UiProfile.PLATFORM
    include_html: bool = False

    def validate(self) -> None:
        if not self.source.is_file():
            raise FileNotFoundError(f"Arquivo MBOX não encontrado: {self.source}")
        if self.source.suffix.lower() != ".mbox":
            raise ValueError("Selecione um arquivo com extensão .mbox.")
        if self.output_root.exists() and not self.output_root.is_dir():
            raise NotADirectoryError(f"O destino selecionado não é uma pasta: {self.output_root}")

    @property
    def settings(self) -> ConversionSettings:
        return ConversionSettings(
            profile=self.profile.destination_profile,
            include_html=self.include_html,
        )


def human_file_size(size_bytes: int) -> str:
    value = float(size_bytes)
    for unit in ("bytes", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            decimals = 0 if unit == "bytes" else 2
            return f"{value:.{decimals}f} {unit}"
        value /= 1024
    raise AssertionError("Unreachable")


def human_duration(seconds: float) -> str:
    total_seconds = max(0, round(seconds))
    minutes, remaining_seconds = divmod(total_seconds, 60)
    if minutes:
        return f"{minutes} min {remaining_seconds:02d} s"
    return f"{remaining_seconds} s"
