from __future__ import annotations


def compact_email_record(record: dict[str, object]) -> dict[str, object]:
    """Remove o envelope técnico e mantém somente contexto útil para análise."""

    data = record.get("data")
    processing = record.get("processing")
    if not isinstance(data, dict):
        raise TypeError("O contrato de e-mail não contém dados válidos")

    output: dict[str, object] = {
        "date": data.get("date"),
        "from": data.get("from") or [],
        "to": data.get("to") or [],
        "subject": data.get("subject"),
        "body": data.get("body_text") or "",
    }
    _copy_nonempty(output, data, "cc")
    _copy_nonempty(output, data, "bcc")
    _copy_nonempty(output, data, "thread_id")

    body_html = data.get("body_html")
    if body_html:
        output["html"] = body_html

    attachments = data.get("attachments")
    if isinstance(attachments, list) and attachments:
        output["attachments"] = [
            {
                key: attachment[key]
                for key in ("file_name", "media_type")
                if key in attachment and attachment[key] not in (None, "")
            }
            for attachment in attachments
            if isinstance(attachment, dict)
        ]

    if isinstance(processing, dict):
        segment_number = processing.get("segment_number")
        segment_count = processing.get("segment_count")
        if isinstance(segment_number, int) and isinstance(segment_count, int):
            output["segment"] = f"{segment_number}/{segment_count}"
    return output


def compact_tabular_record(record: dict[str, object]) -> dict[str, object]:
    """Representa CSV/XLSX sem repetir o envelope de auditoria."""

    source = record.get("source")
    data = record.get("data")
    if not isinstance(source, dict) or not isinstance(data, dict):
        raise TypeError("O contrato tabular está incompleto")
    dataset = data.get("dataset")
    if not isinstance(dataset, dict):
        raise TypeError("O contrato tabular não contém um conjunto de dados")

    columns = dataset.get("columns")
    column_names = (
        [
            column.get("source_name") or column.get("name")
            for column in columns
            if isinstance(column, dict) and column.get("name")
        ]
        if isinstance(columns, list)
        else []
    )

    output: dict[str, object] = {
        "source": source.get("file_name"),
        "rows": {
            "start": dataset.get("row_start"),
            "end": dataset.get("row_end"),
            "total": dataset.get("total_rows"),
        },
        "columns": column_names,
        "data": dataset.get("rows") or [],
    }

    sheet = data.get("sheet")
    if isinstance(sheet, dict):
        output["sheet"] = sheet.get("name")
        if dataset.get("reference"):
            output["range"] = dataset["reference"]

    formulas = data.get("formulas")
    if isinstance(formulas, list) and formulas:
        output["formulas"] = [
            {
                "cell": formula.get("cell_reference"),
                "formula": formula.get("formula"),
            }
            for formula in formulas
            if isinstance(formula, dict)
        ]
    return output


def _copy_nonempty(
    destination: dict[str, object],
    source: dict[str, object],
    key: str,
) -> None:
    value = source.get(key)
    if value not in (None, "", []):
        destination[key] = value
