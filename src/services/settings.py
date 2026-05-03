"""Persistência de configurações e estado da janela usando QSettings."""

from __future__ import annotations

from PyQt6.QtCore import QByteArray, QSettings
from PyQt6.QtWidgets import QMainWindow

_ORG = "MercadoLivreBrowser"
_APP = "CategoryBrowser"


class AppSettings:
    """Persiste configurações e estado da janela principal.

    Usa :class:`QSettings` que armazena no registro (Windows) ou em
    arquivo INI (macOS/Linux) de forma transparente.
    """

    def __init__(self) -> None:
        self._settings = QSettings(_ORG, _APP)

    # ------------------------------------------------------------------
    # Window state
    # ------------------------------------------------------------------

    def save_window_state(self, window: QMainWindow) -> None:
        """Salva posição, tamanho e estado dos painéis da janela."""
        self._settings.setValue("window/geometry", window.saveGeometry())
        self._settings.setValue("window/state", window.saveState())

    def restore_window_state(self, window: QMainWindow) -> None:
        """Restaura posição, tamanho e estado dos painéis da janela."""
        geometry: QByteArray = self._settings.value("window/geometry")  # type: ignore[assignment]
        state: QByteArray = self._settings.value("window/state")  # type: ignore[assignment]
        if geometry:
            window.restoreGeometry(geometry)
        if state:
            window.restoreState(state)

    # ------------------------------------------------------------------
    # Generic key/value
    # ------------------------------------------------------------------

    def get(self, key: str, default=None):
        """Retorna o valor associado a *key*, ou *default* se não existir."""
        return self._settings.value(key, default)

    def set(self, key: str, value) -> None:
        """Armazena *value* associado a *key*."""
        self._settings.setValue(key, value)
