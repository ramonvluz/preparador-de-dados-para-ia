"""Conversores independentes por tipo de fonte."""

from preparador_dados_ia.converters.base import ConversionContext, RecordConverter
from preparador_dados_ia.converters.registry import (
    ConverterRegistrationError,
    ConverterRegistry,
    UnsupportedSourceFormat,
)

__all__ = [
    "ConversionContext",
    "ConverterRegistrationError",
    "ConverterRegistry",
    "RecordConverter",
    "UnsupportedSourceFormat",
]
