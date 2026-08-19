"""Conversão de TXT e Markdown para o contrato textual versionado."""

from preparador_dados_ia.converters.text.converter import TextDocumentConverter
from preparador_dados_ia.converters.text.reader import DecodedText, read_text_source
from preparador_dados_ia.converters.text.structure import TextStructure, analyze_text_structure

__all__ = [
    "DecodedText",
    "TextDocumentConverter",
    "TextStructure",
    "analyze_text_structure",
    "read_text_source",
]
