"""Painel de detalhes da categoria selecionada."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFormLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.models.category import CategoryDTO


class DetailPanel(QWidget):
    """Exibe informações detalhadas da categoria selecionada na árvore.

    Campos exibidos:
    - Nome
    - ID
    - Total de itens
    - Caminho completo desde a raiz (path_from_root)
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._setup_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show_category(self, category: CategoryDTO) -> None:
        """Atualiza o painel com os dados da *category*.

        Args:
            category: Categoria a exibir.
        """
        self._name_label.setText(category.name)
        self._id_label.setText(category.id)
        self._items_label.setText(f"{category.total_items_in_this_category:,}")

        if category.path_from_root:
            path_str = " › ".join(p.get("name", p.get("id", "?")) for p in category.path_from_root)
        else:
            path_str = category.name
        self._path_label.setText(path_str)
        self._path_label.setWordWrap(True)

    def clear(self) -> None:
        """Limpa todos os campos do painel."""
        self._name_label.setText("—")
        self._id_label.setText("—")
        self._items_label.setText("—")
        self._path_label.setText("—")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("<b>Detalhes da Categoria</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        outer_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)

        content = QWidget()
        form = QFormLayout(content)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setContentsMargins(4, 4, 4, 4)
        form.setSpacing(8)

        self._name_label = QLabel("—")
        self._name_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._name_label.setWordWrap(True)

        self._id_label = QLabel("—")
        self._id_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self._items_label = QLabel("—")

        self._path_label = QLabel("—")
        self._path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._path_label.setWordWrap(True)
        self._path_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        form.addRow("<b>Nome:</b>", self._name_label)
        form.addRow("<b>ID:</b>", self._id_label)
        form.addRow("<b>Total de itens:</b>", self._items_label)
        form.addRow("<b>Caminho:</b>", self._path_label)

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)
