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


def write_pdf_readme(
    output_dir: Path,
    *,
    source_name: str,
    converted_records: int,
    part_count: int,
    page_count: int,
    pages_without_text: int,
    embedded_file_count: int,
    image_count: int,
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
        "Tipo identificado: PDF",
        f"Documentos convertidos: {converted_records}",
        f"Páginas catalogadas: {page_count}",
        f"Páginas sem texto incorporado: {pages_without_text}",
        f"Partes geradas: {part_count}",
        "Formato: MARKDOWN",
        "",
        "COMO USAR",
        "Envie os arquivos da pasta PRONTO_PARA_IA em ordem numérica.",
        "Os marcadores LIMEBH_PAGE_START e LIMEBH_PAGE_END preservam a página de origem.",
        "",
        "O QUE ESTÁ INCLUÍDO",
        "Texto incorporado, metadados, sumário e catálogos de imagens e arquivos internos.",
        "",
        "O QUE NÃO ESTÁ INCLUÍDO",
        (
            f"Binários de {embedded_file_count} arquivo(s) incorporado(s) e "
            f"{image_count} imagem(ns) catalogada(s)."
        ),
        "OCR não é aplicado nesta etapa; páginas digitalizadas podem permanecer sem texto.",
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


def write_word_readme(
    output_dir: Path,
    *,
    source_name: str,
    converted_records: int,
    part_count: int,
    block_count: int,
    section_count: int,
    table_count: int,
    image_count: int,
    headers_footers_omitted: bool,
    features_omitted: list[str],
    suspicious_text_sequences: int,
    inferred_headings: int,
    inferred_table_headers: int,
    cancelled: bool,
) -> Path:
    status_line = (
        "A conversão foi cancelada com segurança; somente partes completas foram mantidas."
        if cancelled
        else "A conversão foi concluída."
    )
    omitted = []
    if image_count:
        omitted.append(f"{image_count} imagem(ns)")
    if headers_footers_omitted:
        omitted.append("cabeçalhos e rodapés")
    omitted.extend(features_omitted)
    omitted_line = ", ".join(omitted) if omitted else "nenhum recurso detectado"
    lines = [
        "PREPARADOR DE DADOS PARA IA — LIMEBH",
        "",
        status_line,
        f"Fonte: {source_name}",
        "Tipo identificado: DOCX",
        f"Documentos convertidos: {converted_records}",
        f"Blocos estruturais: {block_count}",
        f"Seções detectadas: {section_count}",
        f"Tabelas preservadas: {table_count}",
        f"Títulos inferidos por formatação: {inferred_headings}",
        f"Cabeçalhos de tabela inferidos: {inferred_table_headers}",
        f"Partes geradas: {part_count}",
        "Formato: MARKDOWN",
        "",
        "COMO USAR",
        "Envie os arquivos da pasta PRONTO_PARA_IA em ordem numérica.",
        "Os marcadores LIMEBH_WORD_BLOCK preservam o intervalo estrutural de origem.",
        "",
        "O QUE ESTÁ INCLUÍDO",
        "Títulos, parágrafos, listas, seções, tabelas simples e metadados do documento.",
        "",
        "O QUE NÃO ESTÁ INCLUÍDO",
        f"Recursos omitidos: {omitted_line}.",
        "Macros, objetos incorporados e reconstrução visual avançada não são processados.",
        "",
        "QUALIDADE DO TEXTO",
        (
            f"ATENÇÃO: foram detectadas {suspicious_text_sequences} sequência(s) de "
            "caracteres suspeita(s) no documento de origem."
            if suspicious_text_sequences
            else "Nenhuma sequência de caracteres suspeita foi detectada."
        ),
        (
            "O texto foi preservado sem correção automática. Revise o documento de origem."
            if suspicious_text_sequences
            else ""
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
