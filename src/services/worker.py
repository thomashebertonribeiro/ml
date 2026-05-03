"""Worker assíncrono para execução de tarefas de rede em thread separada."""

from __future__ import annotations

import logging
from typing import Any, Callable

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

logger = logging.getLogger(__name__)


class _WorkerSignals(QObject):
    """Signals emitidos pelo ApiWorker ao completar ou falhar."""

    finished = pyqtSignal(object)   # resultado da task (qualquer tipo)
    error = pyqtSignal(str)         # mensagem de erro
    progress = pyqtSignal(str)      # mensagem de progresso


class ApiWorker(QRunnable):
    """Executa uma callable em thread separada via QThreadPool.

    Padrão Worker Object: a instância de QRunnable é submetida ao
    QThreadPool, evitando o subclassing de QThread e o problema de
    GUI freeze em execuções subsequentes.

    Args:
        task: Callable a ser executada na thread.
        *args: Argumentos posicionais para *task*.
        **kwargs: Argumentos nomeados para *task*.

    Example::

        worker = ApiWorker(client.get_root_categories)
        worker.signals.finished.connect(on_done)
        worker.signals.error.connect(on_error)
        QThreadPool.globalInstance().start(worker)
    """

    def __init__(self, task: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._task = task
        self._args = args
        self._kwargs = kwargs
        self._cancelled = False
        self.signals = _WorkerSignals()
        # Garante que o worker não seja deletado antes dos signals serem emitidos
        self.setAutoDelete(True)

    def cancel(self) -> None:
        """Sinaliza que o worker deve ser cancelado.

        O cancelamento é cooperativo: a task em execução não é
        interrompida forçosamente, mas o resultado é descartado.
        """
        self._cancelled = True

    def run(self) -> None:
        """Executa a task e emite signals de resultado ou erro."""
        if self._cancelled:
            return
        try:
            self.signals.progress.emit("Carregando...")
            result = self._task(*self._args, **self._kwargs)
            if not self._cancelled:
                self.signals.finished.emit(result)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Erro no ApiWorker: %s", exc)
            if not self._cancelled:
                self.signals.error.emit(str(exc))
