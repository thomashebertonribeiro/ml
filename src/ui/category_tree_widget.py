"""Widget de árvore hierárquica de categorias do Mercado Livre."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem

from src.models.category import CategoryDTO

_COL_NAME = 0
_COL_ID = 1


class CategoryTreeWidget(QTreeWidget):
    """Exibe categorias e subcategorias em estrutura de árvore expansível.

    Signals:
        category_selected: Emitido com o ``category_id`` quando o usuário
            seleciona um nó na árvore.
    """

    category_selected = pyqtSignal(str)  # category_id

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHeaderLabels(["Categoria", "ID"])
        self.setAlternatingRowColors(True)
        self.setAnimated(True)
        self.setSortingEnabled(False)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, self.header().ResizeMode.Stretch)
        self.header().setSectionResizeMode(1, self.header().ResizeMode.ResizeToContents)
        self.itemSelectionChanged.connect(self._on_selection_changed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def populate(self, categories: list[CategoryDTO]) -> None:
        """Popula a árvore com a lista de categorias.

        Reconstrói a hierarquia a partir da lista plana usando ``parent_id``.
        Ordena por nível para garantir que pais sejam criados antes dos filhos.

        Args:
            categories: Lista plana de :class:`CategoryDTO` a exibir.
        """
        self.clear()

        if not categories:
            return

        # Ordena por nível para garantir que pais existam antes dos filhos
        sorted_cats = sorted(categories, key=lambda c: (c.level, c.name))

        # Índice id → item para montagem da hierarquia
        id_to_item: dict[str, QTreeWidgetItem] = {}

        for cat in sorted_cats:
            item = self._make_item(cat)
            id_to_item[cat.id] = item

            if cat.parent_id and cat.parent_id in id_to_item:
                id_to_item[cat.parent_id].addChild(item)
            else:
                self.addTopLevelItem(item)

        # Expande apenas o primeiro nível
        self.expandToDepth(0)
        self.resizeColumnToContents(_COL_ID)

    def expand_node(self, category_id: str) -> None:
        """Expande o nó com o *category_id* informado.

        Args:
            category_id: ID da categoria a expandir.
        """
        items = self.findItems(category_id, Qt.MatchFlag.MatchExactly | Qt.MatchFlag.MatchRecursive, _COL_ID)
        for item in items:
            item.setExpanded(True)

    def clear_tree(self) -> None:
        """Remove todos os itens da árvore."""
        self.clear()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _make_item(self, cat: CategoryDTO) -> QTreeWidgetItem:
        """Cria um QTreeWidgetItem para a categoria."""
        item = QTreeWidgetItem([cat.name, cat.id])
        item.setData(0, Qt.ItemDataRole.UserRole, cat.id)

        # Nós folha: desabilita o indicador de expansão
        if not cat.children_ids:
            item.setChildIndicatorPolicy(
                QTreeWidgetItem.ChildIndicatorPolicy.DontShowIndicatorWhenChildless
            )
        else:
            item.setChildIndicatorPolicy(
                QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
            )

        return item

    def _on_selection_changed(self) -> None:
        """Emite ``category_selected`` com o id do item selecionado."""
        selected = self.selectedItems()
        if selected:
            category_id = selected[0].data(0, Qt.ItemDataRole.UserRole)
            if category_id:
                self.category_selected.emit(category_id)
