from __future__ import annotations

from pathlib import Path


def prepare_output(output_dir: Path) -> Path:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(
            "A pasta de saída já contém arquivos. Use uma pasta nova para não misturar "
            f"resultados: {output_dir}"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    ready_dir = output_dir / "PRONTO_PARA_IA"
    ready_dir.mkdir()
    return ready_dir
