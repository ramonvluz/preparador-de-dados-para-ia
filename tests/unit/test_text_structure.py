from preparador_dados_ia.converters.text.structure import analyze_text_structure


def test_markdown_structure_uses_parser_and_ignores_fenced_code() -> None:
    content = """# Manual

Introdução.

```python
# isto não é título
```

## Procedimento

Execute localmente.
"""

    structure = analyze_text_structure(content, markdown=True)

    assert structure.title == "Manual"
    assert [(item.level, item.text, item.line_number) for item in structure.headings] == [
        (1, "Manual", 1),
        (2, "Procedimento", 9),
    ]
    assert [section.title for section in structure.sections] == ["Manual", "Procedimento"]
    assert "# isto não é título" in structure.sections[0].content


def test_plain_text_structure_detects_conservative_heading_patterns() -> None:
    content = """RELATÓRIO ADMINISTRATIVO

Apresentação do documento.

1. Escopo
Atividades abrangidas.

Responsabilidades
=================
Equipe responsável.
"""

    structure = analyze_text_structure(content, markdown=False)

    assert structure.title == "RELATÓRIO ADMINISTRATIVO"
    assert [(item.level, item.text, item.line_number) for item in structure.headings] == [
        (1, "RELATÓRIO ADMINISTRATIVO", 1),
        (1, "1. Escopo", 5),
        (1, "Responsabilidades", 8),
    ]
    assert structure.sections[-1].content == "Equipe responsável."
    assert structure.sections[-1].start_line == 8
