"""Barra de busca com campo de texto e botões de ação."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget


class SearchBar(QWidget):
    """Barra de busca com campo de texto, botão Buscar e botão Categorias Raiz.

    Signals:
        search_requested: Emitido com o termo de busca quando o usuário
            aciona a busca (botão ou tecla Enter).
        load_roots_requested: Emitido quando o usuário clica em
            "Carregar Categorias Raiz".
    """

    search_requested = pyqtSignal(str)
    load_roots_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._setup_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_busy(self, busy: bool) -> None:
        """Habilita ou desabilita os controles durante operações em andamento.

        Args:
            busy: ``True`` para desabilitar; ``False`` para habilitar.
        """
        self._search_input.setEnabled(not busy)
        self._search_btn.setEnabled(not busy)
        self._roots_btn.setEnabled(not busy)
        if busy:
            self._search_btn.setText("Buscando...")
        else:
            self._search_btn.setText("Buscar")

    def clear(self) -> None:
        """Limpa o campo de texto."""
        self._search_input.clear()

    def get_query(self) -> str:
        """Retorna o texto atual do campo de busca."""
        return self._search_input.text()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Digite uma categoria para buscar...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.returnPressed.connect(self._on_search)

        self._search_btn = QPushButton("Buscar")
        self._search_btn.setDefault(True)
        self._search_btn.clicked.connect(self._on_search)

        self._roots_btn = QPushButton("Carregar Categorias Raiz")
        self._roots_btn.clicked.connect(self.load_roots_requested)

        layout.addWidget(self._search_input, stretch=1)
        layout.addWidget(self._search_btn)
        layout.addWidget(self._roots_btn)

    def _on_search(self) -> None:
        """Emite ``search_requested`` com o texto atual do campo."""
        query = self._search_input.text()
        self.search_requested.emit(query)
