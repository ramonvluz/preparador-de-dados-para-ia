from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from queue import Queue
from threading import Thread

from limebh_preparador.application.naming import automatic_output_dir
from limebh_preparador.application.progress import ConversionProgress
from limebh_preparador.application.service import convert_source
from limebh_preparador.core.cancellation import CancellationToken
from limebh_preparador.ui.state import DesktopConversionRequest


@dataclass(frozen=True, slots=True)
class WorkerStarted:
    output_dir: Path


@dataclass(frozen=True, slots=True)
class WorkerProgress:
    progress: ConversionProgress


@dataclass(frozen=True, slots=True)
class WorkerFinished:
    output_dir: Path
    report: dict[str, object]


@dataclass(frozen=True, slots=True)
class WorkerFailed:
    output_dir: Path | None
    error_type: str
    message: str


WorkerEvent = WorkerStarted | WorkerProgress | WorkerFinished | WorkerFailed


class ConversionWorker:
    """Executa o núcleo fora da thread do Tkinter e publica eventos imutáveis."""

    def __init__(self, events: Queue[WorkerEvent] | None = None) -> None:
        self.events: Queue[WorkerEvent] = events or Queue()
        self._thread: Thread | None = None
        self._token: CancellationToken | None = None

    @property
    def is_active(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, request: DesktopConversionRequest) -> None:
        if self.is_active:
            raise RuntimeError("Já existe uma conversão em andamento.")
        request.validate()
        self._token = CancellationToken()
        self._thread = Thread(
            target=self._run,
            args=(request, self._token),
            name="limebh-conversion-worker",
            daemon=True,
        )
        self._thread.start()

    def cancel(self) -> None:
        if self._token is not None:
            self._token.cancel()

    def wait(self, timeout: float | None = None) -> None:
        if self._thread is not None:
            self._thread.join(timeout)

    def _run(
        self,
        request: DesktopConversionRequest,
        token: CancellationToken,
    ) -> None:
        output_dir: Path | None = None
        try:
            started_at = datetime.now(UTC)
            output_dir = automatic_output_dir(request.source, request.output_root, started_at)
            self.events.put(WorkerStarted(output_dir))
            report = convert_source(
                request.source,
                output_dir,
                settings=request.settings,
                cancellation_token=token,
                progress_callback=lambda progress: self.events.put(WorkerProgress(progress)),
                started_at=started_at,
            )
            self.events.put(WorkerFinished(output_dir, report))
        except Exception as error:
            self.events.put(
                WorkerFailed(
                    output_dir=output_dir,
                    error_type=type(error).__name__,
                    message=str(error),
                )
            )
