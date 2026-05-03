"""Diálogo de exportação de categorias para JSON ou CSV."""

from __future__ import annotations

from PyQt6.QtWidgets import QFileDialog, QWidget


def show_export_dialog(parent: QWidget | None = None) -> tuple[str, str] | None:
    """Exibe um diálogo para o usuário escolher o caminho e formato de exportação.

    Args:
        parent: Widget pai do diálogo.

    Returns:
        Tupla ``(caminho, formato)`` onde formato é ``"json"`` ou ``"csv"``,
        ou ``None`` se o usuário cancelou.
    """
    dialog = QFileDialog(parent, "Exportar Categorias")
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
    dialog.setNameFilters([
        "JSON (*.json)",
        "CSV (*.csv)",
    ])
    dialog.setDefaultSuffix("json")

    if dialog.exec() != QFileDialog.DialogCode.Accepted:
        return None

    selected_files = dialog.selectedFiles()
    if not selected_files:
        return None

    path = selected_files[0]
    selected_filter = dialog.selectedNameFilter()

    if "csv" in selected_filter.lower():
        fmt = "csv"
        if not path.lower().endswith(".csv"):
            path += ".csv"
    else:
        fmt = "json"
        if not path.lower().endswith(".json"):
            path += ".json"

    return path, fmt
