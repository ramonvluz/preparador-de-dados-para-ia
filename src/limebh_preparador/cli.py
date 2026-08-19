from __future__ import annotations

import argparse
import signal
import sys
from datetime import UTC, datetime
from pathlib import Path

from limebh_preparador import __version__
from limebh_preparador.application.conversion import (
    ConversionSettings,
    DestinationProfile,
)
from limebh_preparador.application.naming import (
    automatic_output_dir,
    find_possible_duplicates,
)
from limebh_preparador.application.progress import ConversionProgress
from limebh_preparador.application.service import (
    convert_source,
    source_format_label,
    source_unit_label,
)
from limebh_preparador.core.cancellation import CancellationToken
from limebh_preparador.core.paths import default_output_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepara arquivos MBOX, TXT, Markdown, PDF, DOCX, CSV ou XLSX para uso com IA, "
            "sem enviar dados à internet."
        )
    )
    parser.add_argument("input", type=Path, help="Caminho do arquivo de origem")
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--output", "-o", type=Path, help="Pasta de saída exata")
    output_group.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Pasta-base das conversões automáticas (padrão: Downloads do sistema)",
    )
    parser.add_argument(
        "--profile",
        choices=[profile.value for profile in DestinationProfile],
        default=DestinationProfile.PLATFORM.value,
        help=(
            "Destino: para MBOX, CSV e XLSX, platform gera JSON e api gera JSONL; "
            "documentos narrativos geram Markdown"
        ),
    )
    parser.add_argument("--max-size-mb", type=float, default=50.0)
    parser.add_argument("--max-tokens", type=int, default=500_000)
    parser.add_argument(
        "--include-html",
        action="store_true",
        help="Preserva também o HTML original de fontes MBOX, aumentando a saída",
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def _show_progress(progress: ConversionProgress, source: Path) -> None:
    units = source_unit_label(source, plural=progress.current != 1)
    if progress.stage == "preparing":
        print(f"Preparando o arquivo {source_format_label(source)}...")
    elif progress.stage == "converting" and (
        progress.current == 1 or progress.current % 250 == 0 or progress.current == progress.total
    ):
        participle = (
            "Processadas"
            if source.suffix.lower() in {".mbox", ".pdf", ".csv", ".xlsx"}
            else "Processados"
        )
        amount = (
            f"{progress.current}/{progress.total}"
            if progress.total is not None
            else str(progress.current)
        )
        print(f"{participle} {amount} {units}...")
    elif progress.stage == "writing":
        print("Finalizando partes e relatório...")
    elif progress.stage == "cancelled":
        print(f"Cancelamento concluído após {progress.current} {units}.")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    token = CancellationToken()
    previous_handler = signal.getsignal(signal.SIGINT)

    def request_cancel(_signum: int, _frame: object) -> None:
        token.cancel()
        print("Cancelamento solicitado; concluindo a unidade atual...", file=sys.stderr)

    signal.signal(signal.SIGINT, request_cancel)
    try:
        started_at = datetime.now(UTC)
        input_path = args.input.resolve()
        output_root = (args.output_root or default_output_root()).resolve()
        output_dir = args.output.resolve() if args.output is not None else None
        if output_dir is None:
            for duplicate in find_possible_duplicates(output_root, input_path):
                print(
                    f"Aviso: possível conversão anterior encontrada em {duplicate.resolve()}",
                    file=sys.stderr,
                )
            output_dir = automatic_output_dir(input_path, output_root, started_at)

        report = convert_source(
            input_path,
            output_dir,
            settings=ConversionSettings(
                profile=DestinationProfile(args.profile),
                max_size_mb=args.max_size_mb,
                max_tokens=args.max_tokens,
                include_html=args.include_html,
            ),
            cancellation_token=token,
            progress_callback=lambda progress: _show_progress(progress, input_path),
            started_at=started_at,
        )
    except Exception as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    finally:
        signal.signal(signal.SIGINT, previous_handler)

    converted = int(report.get("converted_records", 0))
    total = int(report.get("total_records", 0))
    failed = int(report.get("failed_records", 0))
    unit = str(report.get("unit_label", "registro"))
    units = unit if total == 1 else ("mensagens" if unit == "mensagem" else f"{unit}s")
    print(
        f"Conversão: {converted}/{total} {units}, "
        f"{len(report['parts'])} parte(s), {failed} falha(s)."
    )
    print(f"Saída: {output_dir}")
    if report["result"] == "cancelled":
        return 130
    return 0 if failed == 0 else 2
