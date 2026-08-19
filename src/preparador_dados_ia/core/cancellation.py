from __future__ import annotations

from dataclasses import dataclass, field
from threading import Event


class ConversionCancelled(Exception):
    """Indica um cancelamento solicitado, sem representar falha de dados."""


@dataclass(slots=True)
class CancellationToken:
    """Sinal de cancelamento seguro para CLI e futura interface desktop."""

    _event: Event = field(default_factory=Event, init=False, repr=False)

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self.is_cancelled:
            raise ConversionCancelled
