"""Janela principal da aplicação Mercado Livre Category Browser."""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from src.models.category import CategoryDTO
from src.repository.category_repository import CategoryRepository
from src.repository.database import DatabaseManager
from src.services.controller import CategoryController
from src.services.ml_client import MercadoLivreClient
from src.services.settings import AppSettings
from src.ui.category_tree_widget import CategoryTreeWidget
from src.ui.detail_panel import DetailPanel
from src.ui.export_dialog import show_export_dialog
from src.ui.import_dialog import ImportDialog
from src.ui.search_bar import SearchBar

logger = logging.getLogger(__name__)

_MIN_WIDTH = 900
_MIN_HEIGHT = 600
_AUTO_REFRESH_INTERVAL_MS = 24 * 60 * 60 * 1000  # 24 horas em ms


class MainWindow(QMainWindow):
    """Janela principal que compõe todos os widgets e conecta signals/slots."""

    def __init__(self, db_manager: DatabaseManager | None = None) -> None:
        super().__init__()
        self.setWindowTitle("Mercado Livre — Explorador de Categorias")
        self.setMinimumSize(_MIN_WIDTH, _MIN_HEIGHT)

        # Infraestrutura
        self._db_manager = db_manager or DatabaseManager()
        self._db_manager.initialize()
        self._repo = CategoryRepository(self._db_manager)
        self._client = MercadoLivreClient()
        self._controller = CategoryController(self._client, self._repo, parent=self)
        self._settings = AppSettings()

        self._setup_ui()
        self._connect_signals()
        self._restore_state()
        self._setup_auto_refresh()

        # Carrega categorias do cache local ao iniciar
        self._controller.load_root_categories()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """Monta o layout principal com splitter horizontal."""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 4)
        main_layout.setSpacing(6)

        # Barra de busca
        self._search_bar = SearchBar()
        main_layout.addWidget(self._search_bar)

        # Barra de ações (atualizar, exportar, contador)
        action_bar = QHBoxLayout()
        action_bar.setSpacing(6)

        self._refresh_btn = QPushButton("🔄 Atualizar Subcategorias")
        self._refresh_btn.setToolTip(
            "Rebusca todas as subcategorias salvas na API do Mercado Livre"
        )

        self._force_refresh_btn = QPushButton("⚡ Forçar Atualização Completa")
        self._force_refresh_btn.setToolTip(
            "Ignora o cache e rebusca TODAS as categorias e subcategorias da API"
        )

        self._import_all_btn = QPushButton("📥 Importar Tudo")
        self._import_all_btn.setToolTip(
            "Importa TODAS as categorias e subcategorias do Mercado Livre Brasil\n"
            "e salva no banco local (pode demorar alguns minutos)"
        )

        self._export_btn = QPushButton("💾 Exportar...")
        self._export_btn.setToolTip("Exportar todas as categorias para JSON ou CSV")

        self._saved_label = QLabel("Salvas: 0")
        self._saved_label.setToolTip("Número de categorias/subcategorias salvas no banco local")

        action_bar.addWidget(self._refresh_btn)
        action_bar.addWidget(self._force_refresh_btn)
        action_bar.addWidget(self._import_all_btn)
        action_bar.addStretch()
        action_bar.addWidget(self._saved_label)
        action_bar.addWidget(self._export_btn)
        main_layout.addLayout(action_bar)

        # Splitter: árvore à esquerda, detalhes à direita
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._tree = CategoryTreeWidget()
        self._detail = DetailPanel()
        self._splitter.addWidget(self._tree)
        self._splitter.addWidget(self._detail)
        self._splitter.setStretchFactor(0, 2)
        self._splitter.setStretchFactor(1, 1)
        main_layout.addWidget(self._splitter, stretch=1)

        # Barra de status
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Pronto.")

    def _connect_signals(self) -> None:
        """Conecta todos os signals aos slots correspondentes."""
        # SearchBar → Controller
        self._search_bar.search_requested.connect(self._on_search_requested)
        self._search_bar.load_roots_requested.connect(self._controller.load_root_categories)

        # Botões de ação
        self._refresh_btn.clicked.connect(self._on_refresh)
        self._force_refresh_btn.clicked.connect(self._on_force_refresh)
        self._import_all_btn.clicked.connect(self._on_import_all)
        self._export_btn.clicked.connect(self._on_export)

        # Controller → UI
        self._controller.search_completed.connect(self._on_categories_loaded)
        self._controller.load_completed.connect(self._on_categories_loaded)
        self._controller.error_occurred.connect(self._on_error)
        self._controller.progress_changed.connect(self._on_progress)

        # Árvore → Painel de detalhes
        self._tree.category_selected.connect(self._on_category_selected)

    def _setup_auto_refresh(self) -> None:
        """Configura o timer de atualização automática a cada 24 horas."""
        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.setInterval(_AUTO_REFRESH_INTERVAL_MS)
        self._auto_refresh_timer.timeout.connect(self._on_auto_refresh)
        self._auto_refresh_timer.start()
        logger.info("Timer de atualização automática configurado (24h)")

    def _restore_state(self) -> None:
        """Restaura geometria e estado dos painéis da sessão anterior."""
        self._settings.restore_window_state(self)

    def _save_state(self) -> None:
        """Salva geometria e estado dos painéis."""
        self._settings.save_window_state(self)

    def _update_saved_count(self) -> None:
        """Atualiza o contador de categorias salvas."""
        count = self._controller.get_saved_count()
        self._saved_label.setText(f"Salvas: {count:,}")

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_search_requested(self, query: str) -> None:
        self._search_bar.set_busy(True)
        self._detail.clear()
        self._controller.search(query)

    def _on_categories_loaded(self, categories: list) -> None:
        self._search_bar.set_busy(False)
        self._set_buttons_busy(False)
        self._tree.populate(categories)
        self._update_saved_count()

    def _on_category_selected(self, category_id: str) -> None:
        """Busca detalhes da categoria selecionada e exibe no painel."""
        cat = self._repo.get_by_id(category_id)
        if cat:
            self._detail.show_category(cat)
        else:
            from PyQt6.QtCore import QThreadPool
            from src.services.worker import ApiWorker

            def _fetch():
                return self._client.get_category_detail(category_id)

            worker = ApiWorker(_fetch)
            worker.signals.finished.connect(
                lambda detail: (self._repo.upsert(detail), self._detail.show_category(detail))
            )
            worker.signals.error.connect(self._on_error)
            QThreadPool.globalInstance().start(worker)

    def _on_import_all(self) -> None:
        """Importa todas as categorias e subcategorias do ML Brasil."""
        reply = QMessageBox.question(
            self,
            "Importar Todas as Categorias",
            "Isso vai buscar e salvar <b>todas</b> as categorias e subcategorias "
            "do Mercado Livre Brasil.<br><br>"
            "O processo pode levar <b>5 a 15 minutos</b> dependendo da sua conexão.<br><br>"
            "Deseja continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Cria e exibe o diálogo de progresso
        self._import_dialog = ImportDialog(self)

        # Conecta signals do controller ao diálogo
        self._controller.import_progress.connect(self._import_dialog.on_import_progress)
        self._controller.import_finished.connect(self._import_dialog.on_import_finished)
        self._controller.error_occurred.connect(self._import_dialog.on_error)

        # Inicia a importação
        self._set_buttons_busy(True)
        self._controller.import_all_categories(delay_ms=150)

        # Exibe o diálogo (bloqueante — fecha quando terminar ou cancelar)
        self._import_dialog.exec()

        # Se cancelou, para o worker
        if self._import_dialog.is_cancelled():
            self._controller.cancel_current_operation()
            self._status_bar.showMessage("Importação cancelada.", 5000)
            self._set_buttons_busy(False)

    def _on_refresh(self) -> None:
        """Atualiza apenas as categorias obsoletas (> 24h)."""
        saved = self._controller.get_saved_count()
        if saved == 0:
            QMessageBox.information(
                self,
                "Nenhuma categoria salva",
                "Faça uma busca primeiro para salvar categorias no banco local.",
            )
            return
        self._set_buttons_busy(True)
        self._status_bar.showMessage("Iniciando atualização das subcategorias...")
        self._controller.refresh_all(force=False)

    def _on_force_refresh(self) -> None:
        """Força atualização completa de todas as categorias."""
        saved = self._controller.get_saved_count()
        msg = (
            f"Isso vai rebuscar TODAS as {saved:,} categorias e subcategorias "
            "salvas na API do Mercado Livre.\n\n"
            "Pode demorar vários minutos dependendo da quantidade de dados.\n\n"
            "Deseja continuar?"
        )
        reply = QMessageBox.question(
            self,
            "Forçar Atualização Completa",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._set_buttons_busy(True)
        self._status_bar.showMessage("Iniciando atualização completa...")
        self._controller.refresh_all(force=True)

    def _on_auto_refresh(self) -> None:
        """Atualização automática silenciosa a cada 24 horas."""
        saved = self._controller.get_saved_count()
        if saved == 0:
            return
        logger.info("Iniciando atualização automática (24h)")
        self._status_bar.showMessage("Atualização automática em andamento...", 5000)
        self._controller.refresh_all(force=False)

    def _on_error(self, message: str) -> None:
        self._search_bar.set_busy(False)
        self._set_buttons_busy(False)
        self._status_bar.showMessage(f"⚠ {message}", 8000)
        logger.error("Erro exibido ao usuário: %s", message)

    def _on_progress(self, message: str) -> None:
        self._status_bar.showMessage(message, 5000)

    def _on_export(self) -> None:
        result = show_export_dialog(self)
        if result is None:
            return
        path, fmt = result
        self._controller.export_data(path, fmt)

    def _set_buttons_busy(self, busy: bool) -> None:
        """Habilita/desabilita botões de ação durante operações longas."""
        self._refresh_btn.setEnabled(not busy)
        self._force_refresh_btn.setEnabled(not busy)
        self._import_all_btn.setEnabled(not busy)
        self._export_btn.setEnabled(not busy)
        if busy:
            self._refresh_btn.setText("⏳ Atualizando...")
            self._force_refresh_btn.setText("⏳ Atualizando...")
            self._import_all_btn.setText("⏳ Importando...")
        else:
            self._refresh_btn.setText("🔄 Atualizar Subcategorias")
            self._force_refresh_btn.setText("⚡ Forçar Atualização Completa")
            self._import_all_btn.setText("📥 Importar Tudo")

    # ------------------------------------------------------------------
    # Window lifecycle
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        """Salva estado e fecha conexão com o banco ao fechar a janela."""
        self._save_state()
        self._auto_refresh_timer.stop()
        self._controller.cancel_current_operation()
        self._db_manager.close()
        super().closeEvent(event)
