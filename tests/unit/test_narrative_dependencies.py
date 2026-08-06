from importlib.metadata import version

from charset_normalizer import from_bytes
from docx import Document
from markdown_it import MarkdownIt
from pypdf import PdfReader
from reportlab.pdfgen import canvas


def test_approved_narrative_stack_is_available() -> None:
    assert version("charset-normalizer").startswith("3.")
    assert version("markdown-it-py").startswith("4.")
    assert version("pypdf").startswith("6.")
    assert version("python-docx").startswith("1.")
    assert version("reportlab").startswith("4.")
    assert callable(from_bytes)
    assert callable(MarkdownIt)
    assert callable(PdfReader)
    assert callable(Document)
    assert callable(canvas.Canvas)
