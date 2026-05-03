"""Ponto de entrada da aplicação Mercado Livre Category Browser."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from src.services.exceptions import StorageError
from src.services.logger import setup_logging


def main() -> int:
    """Inicializa e executa a aplicação.

    Returns:
        Código de saída do processo (0 = sucesso).
    """
    # Configura logging antes de qualquer outra coisa
    setup_logging()

    app = QApplication(sys.argv)
    app.setApplicationName("Mercado Livre Category Browser")
    app.setOrganizationName("MercadoLivreBrowser")

    # Importação tardia para garantir que QApplication existe antes de
    # qualquer widget ser criado
    from src.repository.database import DatabaseManager
    from src.ui.main_window import MainWindow

    db_manager = DatabaseManager()

    try:
        db_manager.initialize()
    except StorageError as exc:
        QMessageBox.warning(
            None,
            "Banco de dados inacessível",
            f"Não foi possível inicializar o banco de dados local:\n{exc}\n\n"
            "A aplicação será iniciada sem dados salvos.",
        )
        # Continua com banco em memória como fallback
        db_manager = DatabaseManager(":memory:")
        db_manager.initialize()
    except Exception as exc:  # noqa: BLE001
        QMessageBox.warning(
            None,
            "Aviso de inicialização",
            f"Erro inesperado ao inicializar o banco de dados:\n{exc}\n\n"
            "A aplicação será iniciada sem dados salvos.",
        )
        db_manager = DatabaseManager(":memory:")
        db_manager.initialize()

    window = MainWindow(db_manager=db_manager)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
