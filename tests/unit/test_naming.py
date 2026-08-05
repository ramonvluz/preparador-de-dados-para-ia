from datetime import UTC, datetime
from pathlib import Path

from limebh_preparador.application.naming import automatic_output_dir, slugify_filename


def test_automatic_output_name_is_local_and_collision_safe(tmp_path: Path) -> None:
    source = Path("Todos os e-mails, incluindo Spam.mbox")
    started = datetime(2026, 8, 5, 13, 30, 45, tzinfo=UTC)
    timestamp = started.astimezone().strftime("%Y%m%d_%H%M%S")

    assert slugify_filename(source) == "todos_os_e_mails_incluindo_spam"
    first = automatic_output_dir(source, tmp_path, started)
    assert first == tmp_path / f"todos_os_e_mails_incluindo_spam__{timestamp}"
    first.mkdir()
    assert automatic_output_dir(source, tmp_path, started).name.endswith("__02")
