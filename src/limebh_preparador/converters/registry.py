from __future__ import annotations

from pathlib import Path

from limebh_preparador.converters.base import RecordConverter


class ConverterRegistrationError(ValueError):
    """Indica uma configuração ambígua ou incompleta do registro."""


class UnsupportedSourceFormat(ValueError):
    """Indica que nenhuma extensão registrada atende à fonte."""


class ConverterRegistry:
    """Resolve conversores por extensão sem acoplar o núcleo às bibliotecas de leitura."""

    def __init__(self) -> None:
        self._by_id: dict[str, RecordConverter] = {}
        self._by_extension: dict[str, RecordConverter] = {}

    def register(self, converter: RecordConverter) -> None:
        converter_id = converter.converter_id.strip()
        record_type = converter.record_type.strip()
        if not converter_id or not record_type:
            raise ConverterRegistrationError(
                "Identificador do conversor e tipo de registro são obrigatórios"
            )
        if converter_id in self._by_id:
            raise ConverterRegistrationError(f"Conversor já registrado: {converter_id}")

        extensions = {_normalize_extension(value) for value in converter.supported_extensions}
        if not extensions:
            raise ConverterRegistrationError("O conversor deve declarar ao menos uma extensão")

        conflicts = sorted(extension for extension in extensions if extension in self._by_extension)
        if conflicts:
            joined = ", ".join(conflicts)
            raise ConverterRegistrationError(f"Extensão já registrada: {joined}")

        self._by_id[converter_id] = converter
        for extension in extensions:
            self._by_extension[extension] = converter

    def resolve(self, source: Path) -> RecordConverter:
        extension = source.suffix.lower()
        converter = self._by_extension.get(extension)
        if converter is None:
            label = extension or "<sem extensão>"
            raise UnsupportedSourceFormat(f"Formato de fonte não suportado: {label}")
        return converter

    def get(self, converter_id: str) -> RecordConverter:
        try:
            return self._by_id[converter_id]
        except KeyError as error:
            raise KeyError(f"Conversor não registrado: {converter_id}") from error

    @property
    def supported_extensions(self) -> tuple[str, ...]:
        return tuple(sorted(self._by_extension))

    @property
    def converters(self) -> tuple[RecordConverter, ...]:
        return tuple(self._by_id.values())


def _normalize_extension(value: str) -> str:
    extension = value.strip().lower()
    if not extension:
        raise ConverterRegistrationError("Extensões vazias não são permitidas")
    if "/" in extension or "\\" in extension:
        raise ConverterRegistrationError(f"Extensão inválida: {value}")
    if not extension.startswith("."):
        extension = f".{extension}"
    return extension
