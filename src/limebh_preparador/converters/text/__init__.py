"""Conversão de TXT e Markdown para o contrato textual versionado."""

from limebh_preparador.converters.text.converter import TextDocumentConverter
from limebh_preparador.converters.text.reader import DecodedText, read_text_source
from limebh_preparador.converters.text.structure import TextStructure, analyze_text_structure

__all__ = [
    "DecodedText",
    "TextDocumentConverter",
    "TextStructure",
    "analyze_text_structure",
    "read_text_source",
]
