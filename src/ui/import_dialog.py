"""Diálogo de importação completa de todas as categorias do Mercado Livre."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)


class ImportDialog(QDialog):
    """Diálogo modal que exibe o progresso da importação completa.

    Mostra:
    - Barra de progresso por categoria raiz
    - Nome da categoria sendo processada
    - Contador de subcategorias salvas
    - Botão Cancelar (durante a importação) / Fechar (ao concluir)
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Importar Todas as Categorias")
        self.setMinimumWidth(480)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self._cancelled = False
        self._setup_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_cancelled(self) -> bool:
        return self._cancelled

    @pyqtSlot(int, int, str, int)
    def on_import_progress(
        self,
        current: int,
        total: int,
        root_name: str,
        saved: int,
    ) -> None:
        """Atualiza o diálogo com o progresso atual."""
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(current)
        self._root_label.setText(f"Processando: <b>{root_name}</b>")
        self._counter_label.setText(
            f"Categoria {current} de {total} — {saved:,} subcategorias salvas"
        )

    @pyqtSlot(int)
    def on_import_finished(self, total_saved: int) -> None:
        """Chamado quando a importação termina com sucesso."""
        self._progress_bar.setValue(self._progress_bar.maximum())
        self._root_label.setText("✅ Importação concluída!")
        self._counter_label.setText(
            f"<b>{total_saved:,}</b> categorias e subcategorias salvas no banco local."
        )
        self._cancel_btn.setText("Fechar")
        self._cancel_btn.clicked.disconnect()
        self._cancel_btn.clicked.connect(self.accept)

    @pyqtSlot(str)
    def on_error(self, message: str) -> None:
        """Chamado em caso de erro durante a importação."""
        self._root_label.setText(f"⚠ Erro: {message}")
        self._cancel_btn.setText("Fechar")
        self._cancel_btn.clicked.disconnect()
        self._cancel_btn.clicked.connect(self.reject)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel(
            "<b>Importando todas as categorias do Mercado Livre Brasil</b><br>"
            "<small>Isso pode levar alguns minutos. Não feche a janela.</small>"
        )
        title.setWordWrap(True)
        layout.addWidget(title)

        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(31)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%v de %m categorias raiz")
        layout.addWidget(self._progress_bar)

        self._root_label = QLabel("Iniciando...")
        self._root_label.setWordWrap(True)
        layout.addWidget(self._root_label)

        self._counter_label = QLabel("0 subcategorias salvas")
        self._counter_label.setStyleSheet("color: gray;")
        layout.addWidget(self._counter_label)

        self._cancel_btn = QPushButton("Cancelar")
        self._cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(self._cancel_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _on_cancel(self) -> None:
        self._cancelled = True
        self._root_label.setText("⏹ Cancelando...")
        self._cancel_btn.setEnabled(False)
        self.reject()
