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
    convert_mbox,
)
from limebh_preparador.application.naming import (
    automatic_output_dir,
    find_possible_duplicates,
)
from limebh_preparador.application.progress import ConversionProgress
from limebh_preparador.core.cancellation import CancellationToken
from limebh_preparador.core.paths import default_output_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepara um arquivo MBOX para uso com IA, sem enviar dados à internet."
    )
    parser.add_argument("input", type=Path, help="Caminho do arquivo .mbox")
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
        help="Destino: platform gera JSON; api gera JSONL (padrão: platform)",
    )
    parser.add_argument("--max-size-mb", type=float, default=50.0)
    parser.add_argument("--max-tokens", type=int, default=500_000)
    parser.add_argument(
        "--include-html",
        action="store_true",
        help="Preserva também o HTML original, aumentando a saída",
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def _show_progress(progress: ConversionProgress) -> None:
    if progress.stage == "preparing":
        print("Preparando o arquivo MBOX...")
    elif progress.stage == "converting" and (progress.current == 1 or progress.current % 250 == 0):
        print(f"Processadas {progress.current} mensagens...")
    elif progress.stage == "writing":
        print("Finalizando partes e relatório...")
    elif progress.stage == "cancelled":
        print(f"Cancelamento concluído após {progress.current} mensagens.")


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

        report = convert_mbox(
            input_path,
            output_dir,
            settings=ConversionSettings(
                profile=DestinationProfile(args.profile),
                max_size_mb=args.max_size_mb,
                max_tokens=args.max_tokens,
                include_html=args.include_html,
            ),
            cancellation_token=token,
            progress_callback=_show_progress,
            started_at=started_at,
        )
    except Exception as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    finally:
        signal.signal(signal.SIGINT, previous_handler)

    print(
        f"Conversão: {report['converted_messages']}/{report['total_messages']} mensagens, "
        f"{len(report['parts'])} parte(s), {report['failed_messages']} falha(s)."
    )
    print(f"Saída: {output_dir}")
    if report["result"] == "cancelled":
        return 130
    return 0 if report["failed_messages"] == 0 else 2
