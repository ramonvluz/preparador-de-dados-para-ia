from __future__ import annotations

from pathlib import Path

from limebh_preparador.outputs.atomic import atomic_write_json, atomic_write_text
from limebh_preparador.outputs.parts import OutputFormat


def write_readme(
    output_dir: Path,
    *,
    source_name: str,
    converted_messages: int,
    part_count: int,
    attachment_count: int,
    output_format: OutputFormat,
    cancelled: bool,
) -> Path:
    status_line = (
        "A conversão foi cancelada com segurança; somente partes completas foram mantidas."
        if cancelled
        else "A conversão foi concluída."
    )
    lines = [
        "PREPARADOR DE DADOS PARA IA — LIMEBH",
        "",
        status_line,
        f"Fonte: {source_name}",
        f"Mensagens convertidas: {converted_messages}",
        f"Partes geradas: {part_count}",
        f"Formato: {output_format.value.upper()}",
        "",
        "COMO USAR",
        "Envie os arquivos da pasta PRONTO_PARA_IA em ordem numérica.",
        "",
        "O QUE ESTÁ INCLUÍDO",
        "Texto, assunto, data, participantes, labels, threads, referências e metadados de anexos.",
        "",
        "O QUE NÃO ESTÁ INCLUÍDO",
        (
            f"Os binários dos anexos ({attachment_count} anexo(s) catalogado(s)) "
            "e seu conteúdo interno."
        ),
        "",
        "PRIVACIDADE",
        (
            "A saída pode conter dados pessoais. Compartilhe apenas com pessoas "
            "e serviços autorizados."
        ),
    ]
    path = output_dir / "LEIA-ME.txt"
    atomic_write_text(path, "\n".join(lines) + "\n")
    return path


def write_report(output_dir: Path, report: dict[str, object]) -> Path:
    path = output_dir / "relatorio_conversao.json"
    atomic_write_json(path, report)
    return path


def write_document_readme(
    output_dir: Path,
    *,
    source_name: str,
    source_type: str,
    converted_records: int,
    part_count: int,
    encoding: str | None,
    cancelled: bool,
) -> Path:
    status_line = (
        "A conversão foi cancelada com segurança; somente partes completas foram mantidas."
        if cancelled
        else "A conversão foi concluída."
    )
    encoding_line = encoding or "não identificada"
    lines = [
        "PREPARADOR DE DADOS PARA IA — LIMEBH",
        "",
        status_line,
        f"Fonte: {source_name}",
        f"Tipo identificado: {source_type}",
        f"Codificação identificada: {encoding_line}",
        f"Documentos convertidos: {converted_records}",
        f"Partes geradas: {part_count}",
        "Formato: MARKDOWN",
        "",
        "COMO USAR",
        "Envie os arquivos da pasta PRONTO_PARA_IA em ordem numérica.",
        "",
        "O QUE ESTÁ INCLUÍDO",
        "Texto limpo, metadados da fonte e referências aos intervalos de linhas.",
        "",
        "O QUE NÃO ESTÁ INCLUÍDO",
        "Imagens, anexos ou outros arquivos eventualmente mencionados no texto.",
        "",
        "PRIVACIDADE",
        (
            "A saída pode conter dados pessoais. Compartilhe apenas com pessoas "
            "e serviços autorizados."
        ),
    ]
    path = output_dir / "LEIA-ME.txt"
    atomic_write_text(path, "\n".join(lines) + "\n")
    return path
