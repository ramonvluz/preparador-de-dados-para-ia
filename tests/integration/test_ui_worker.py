from pathlib import Path
from queue import Empty

from openpyxl import Workbook

from preparador_dados_ia.ui.state import DesktopConversionRequest, UiProfile
from preparador_dados_ia.ui.worker import (
    ConversionWorker,
    WorkerEvent,
    WorkerFinished,
    WorkerProgress,
    WorkerStarted,
)

PROJECT_ROOT = Path(__file__).parents[2]
FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "artificial_emails.mbox"
PDF_FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "artificial_document.pdf"
WORD_FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "artificial_document.docx"


def _drain_events(worker: ConversionWorker) -> list[WorkerEvent]:
    events: list[WorkerEvent] = []
    while True:
        try:
            events.append(worker.events.get_nowait())
        except Empty:
            return events


def test_worker_runs_core_outside_calling_thread(tmp_path: Path) -> None:
    worker = ConversionWorker()
    request = DesktopConversionRequest(
        source=FIXTURE,
        output_root=tmp_path,
        profile=UiProfile.PLATFORM,
    )

    worker.start(request)
    worker.wait(timeout=10)
    events = _drain_events(worker)

    assert worker.is_active is False
    started = next(event for event in events if isinstance(event, WorkerStarted))
    finished = next(event for event in events if isinstance(event, WorkerFinished))
    progress_events = [event for event in events if isinstance(event, WorkerProgress)]
    assert finished.output_dir == started.output_dir
    assert finished.report["converted_messages"] == 2
    assert finished.report["failed_messages"] == 0
    assert progress_events
    assert (finished.output_dir / "PRONTO_PARA_IA").is_dir()
    assert (finished.output_dir / "relatorio_conversao.json").is_file()


def test_worker_dispatches_markdown_without_blocking_calling_thread(tmp_path: Path) -> None:
    source = tmp_path / "manual.md"
    source.write_text("# Manual\n\nConteúdo local.", encoding="utf-8")
    worker = ConversionWorker()
    request = DesktopConversionRequest(source=source, output_root=tmp_path)

    worker.start(request)
    worker.wait(timeout=10)
    events = _drain_events(worker)

    finished = next(event for event in events if isinstance(event, WorkerFinished))
    assert worker.is_active is False
    assert finished.report["converted_records"] == 1
    assert finished.report["output_format"] == "markdown"
    assert list((finished.output_dir / "PRONTO_PARA_IA").glob("*.md"))


def test_worker_dispatches_pdf_and_reports_page_progress(tmp_path: Path) -> None:
    worker = ConversionWorker()
    request = DesktopConversionRequest(source=PDF_FIXTURE, output_root=tmp_path)

    worker.start(request)
    worker.wait(timeout=10)
    events = _drain_events(worker)

    finished = next(event for event in events if isinstance(event, WorkerFinished))
    progress = [event for event in events if isinstance(event, WorkerProgress)]
    assert worker.is_active is False
    assert finished.report["pdf_extraction"]["page_count"] == 3
    assert any(event.progress.current == 3 for event in progress)
    assert list((finished.output_dir / "PRONTO_PARA_IA").glob("*.md"))


def test_worker_dispatches_word_and_reports_structural_blocks(tmp_path: Path) -> None:
    worker = ConversionWorker()
    request = DesktopConversionRequest(source=WORD_FIXTURE, output_root=tmp_path)

    worker.start(request)
    worker.wait(timeout=10)
    events = _drain_events(worker)

    finished = next(event for event in events if isinstance(event, WorkerFinished))
    progress = [event for event in events if isinstance(event, WorkerProgress)]
    assert worker.is_active is False
    assert finished.report["word_extraction"]["block_count"] == 18
    assert any(event.progress.stage == "converting" for event in progress)
    assert list((finished.output_dir / "PRONTO_PARA_IA").glob("*.md"))


def test_worker_dispatches_csv_and_reports_rows(tmp_path: Path) -> None:
    source = tmp_path / "dados.csv"
    source.write_text("Código,Valor\n1,10\n2,20\n", encoding="utf-8")
    worker = ConversionWorker()
    request = DesktopConversionRequest(source=source, output_root=tmp_path)

    worker.start(request)
    worker.wait(timeout=10)
    events = _drain_events(worker)

    finished = next(event for event in events if isinstance(event, WorkerFinished))
    progress = [event for event in events if isinstance(event, WorkerProgress)]
    assert worker.is_active is False
    assert finished.report["converted_records"] == 2
    assert finished.report["tabular_extraction"]["columns"] == 2
    assert any(event.progress.current == 2 for event in progress)
    assert list((finished.output_dir / "PRONTO_PARA_IA").glob("*.json"))


def test_worker_dispatches_xlsx_and_reports_sheets(tmp_path: Path) -> None:
    source = tmp_path / "dados.xlsx"
    workbook = Workbook()
    workbook.active.append(["Código", "Valor"])
    workbook.active.append(["001", 10])
    workbook.save(source)
    workbook.close()
    worker = ConversionWorker()
    request = DesktopConversionRequest(source=source, output_root=tmp_path)

    worker.start(request)
    worker.wait(timeout=10)
    events = _drain_events(worker)

    finished = next(event for event in events if isinstance(event, WorkerFinished))
    assert finished.report["converted_records"] == 1
    assert finished.report["spreadsheet_extraction"]["sheets"] == 1
    assert list((finished.output_dir / "PRONTO_PARA_IA").glob("*.json"))
