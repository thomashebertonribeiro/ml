"""CategoryController — orquestra a lógica entre UI, API e repositório."""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import QObject, QThreadPool, pyqtSignal

from src.models.category import CategoryDTO
from src.repository.category_repository import CategoryRepository
from src.services.exceptions import StorageError, ValidationError
from src.services.ml_client import MercadoLivreClient
from src.services.validation import validate_search_query
from src.services.worker import ApiWorker

logger = logging.getLogger(__name__)


def _bfs_from_cache(
    repo: CategoryRepository,
    root_id: str,
    visited: set[str],
) -> list[CategoryDTO]:
    """BFS no banco local a partir de *root_id*, respeitando *visited*."""
    result: list[CategoryDTO] = []
    queue = [root_id]
    while queue:
        current_id = queue.pop(0)
        if current_id in visited:
            continue
        visited.add(current_id)
        node = repo.get_by_id(current_id)
        if node:
            result.append(node)
            for child in repo.get_children(current_id):
                if child.id not in visited:
                    queue.append(child.id)
    return result


class CategoryController(QObject):
    """Orquestra buscas, carregamento e exportação de categorias."""

    search_completed = pyqtSignal(list)
    load_completed   = pyqtSignal(list)
    error_occurred   = pyqtSignal(str)
    progress_changed = pyqtSignal(str)
    import_progress  = pyqtSignal(int, int, str, int)  # idx, total, name, saved
    import_finished  = pyqtSignal(int)                 # total salvo

    def __init__(
        self,
        client: MercadoLivreClient,
        repository: CategoryRepository,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._client = client
        self._repo = repository
        self._thread_pool = QThreadPool.globalInstance()
        self._current_worker: Optional[ApiWorker] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(self, query: str) -> None:
        """Busca categorias pelo termo e toda a árvore de subcategorias."""
        try:
            validate_search_query(query)
        except ValidationError as exc:
            self.error_occurred.emit(str(exc))
            return

        cached = self._repo.search_local(query)
        has_subcategories = any(cat.level > 0 for cat in cached)
        if cached and has_subcategories:
            stale = any(self._repo.is_stale(cat.id) for cat in cached)
            if not stale:
                logger.debug("Cache hit para '%s' (%d nós)", query, len(cached))
                self.search_completed.emit(self._get_full_tree_from_cache(cached))
                return

        self.cancel_current_operation()

        client = self._client
        repo = self._repo
        progress_signal = self.progress_changed

        def _task() -> list[CategoryDTO]:
            categories = client.search_categories(query)
            if not categories and query.upper().startswith("MLB"):
                try:
                    categories = [client.get_category_detail(query.upper())]
                except Exception:  # noqa: BLE001
                    pass
            if not categories:
                return []

            all_nodes: list[CategoryDTO] = []
            visited_roots: set[str] = set()
            for cat in categories:
                try:
                    detail = client.get_category_detail(cat.id)
                except Exception:  # noqa: BLE001
                    detail = None
                root_id = (
                    detail.path_from_root[0]["id"]
                    if detail and detail.path_from_root
                    else cat.id
                )
                if root_id in visited_roots:
                    continue
                visited_roots.add(root_id)
                tree_nodes = client.fetch_full_tree(
                    root_id,
                    progress_callback=lambda msg: progress_signal.emit(msg),
                )
                for node in tree_nodes:
                    try:
                        repo.upsert(node)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Erro ao persistir %s: %s", node.id, exc)
                all_nodes.extend(tree_nodes)
            return all_nodes

        worker = ApiWorker(_task)
        worker.signals.finished.connect(self._on_search_finished)
        worker.signals.error.connect(self._on_error)
        worker.signals.progress.connect(self.progress_changed)
        self._current_worker = worker
        self._thread_pool.start(worker)

    def load_root_categories(self) -> None:
        """Carrega as categorias raiz do MLB (cache ou API)."""
        cached = self._repo.get_children(None)
        if cached:
            stale = any(self._repo.is_stale(cat.id) for cat in cached)
            if not stale:
                logger.debug("Carregando %d raízes do cache", len(cached))
                self.load_completed.emit(cached)
                return

        self.cancel_current_operation()

        client = self._client
        repo = self._repo

        def _task() -> list[CategoryDTO]:
            roots = client.get_root_categories()
            for cat in roots:
                repo.upsert(cat)
            return roots

        worker = ApiWorker(_task)
        worker.signals.finished.connect(self._on_load_finished)
        worker.signals.error.connect(self._on_error)
        worker.signals.progress.connect(self.progress_changed)
        self._current_worker = worker
        self._thread_pool.start(worker)

    def refresh_all(self, force: bool = False) -> None:
        """Atualiza todas as categorias salvas rebuscando da API."""
        self.cancel_current_operation()

        client = self._client
        repo = self._repo
        progress_signal = self.progress_changed

        def _task() -> list[CategoryDTO]:
            roots = repo.get_children(None)
            if not roots:
                roots = client.get_root_categories()
                for r in roots:
                    repo.upsert(r)
            total = len(roots)
            all_nodes: list[CategoryDTO] = []
            visited: set[str] = set()
            for idx, root in enumerate(roots, 1):
                if not force and not repo.is_stale(root.id):
                    all_nodes.extend(_bfs_from_cache(repo, root.id, visited))
                    progress_signal.emit(f"[{idx}/{total}] {root.name} — cache válido")
                    continue
                progress_signal.emit(f"[{idx}/{total}] Atualizando: {root.name}...")
                tree_nodes = client.fetch_full_tree(
                    root.id,
                    progress_callback=lambda msg: progress_signal.emit(msg),
                    visited=visited,
                )
                for node in tree_nodes:
                    try:
                        repo.upsert(node)
                        visited.add(node.id)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Erro ao persistir %s: %s", node.id, exc)
                all_nodes.extend(tree_nodes)
            return all_nodes

        worker = ApiWorker(_task)
        worker.signals.finished.connect(self._on_refresh_finished)
        worker.signals.error.connect(self._on_error)
        worker.signals.progress.connect(self.progress_changed)
        self._current_worker = worker
        self._thread_pool.start(worker)

    def import_all_categories(self, delay_ms: int = 150) -> None:
        """Importa TODAS as categorias e subcategorias do Mercado Livre Brasil."""
        self.cancel_current_operation()

        client = self._client
        repo = self._repo
        progress_signal = self.progress_changed
        import_progress_signal = self.import_progress

        def _task() -> list[CategoryDTO]:
            roots = client.get_root_categories()
            total_roots = len(roots)
            all_nodes: list[CategoryDTO] = []
            visited: set[str] = set()
            total_saved = 0

            for idx, root in enumerate(roots, 1):
                import_progress_signal.emit(idx, total_roots, root.name, total_saved)
                progress_signal.emit(f"[{idx}/{total_roots}] Importando: {root.name}...")

                tree_nodes = client.fetch_full_tree(
                    root.id,
                    progress_callback=lambda msg: progress_signal.emit(msg),
                    visited=visited,
                    delay_ms=delay_ms,
                )
                for node in tree_nodes:
                    try:
                        repo.upsert(node)
                        visited.add(node.id)
                        total_saved += 1
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Erro ao persistir %s: %s", node.id, exc)
                all_nodes.extend(tree_nodes)
                import_progress_signal.emit(idx, total_roots, root.name, total_saved)

            return all_nodes

        worker = ApiWorker(_task)
        worker.signals.finished.connect(self._on_import_finished)
        worker.signals.error.connect(self._on_error)
        worker.signals.progress.connect(self.progress_changed)
        self._current_worker = worker
        self._thread_pool.start(worker)

    def cancel_current_operation(self) -> None:
        """Cancela o worker em andamento, se houver."""
        if self._current_worker is not None:
            self._current_worker.cancel()
            self._current_worker = None

    def get_saved_count(self) -> int:
        """Retorna o número de categorias salvas no banco local."""
        return len(self._repo.get_all())

    def export_data(self, path: str, fmt: str) -> None:
        """Exporta todas as categorias para arquivo JSON ou CSV."""
        try:
            if fmt.lower() == "json":
                self._repo.export_json(path)
            elif fmt.lower() == "csv":
                self._repo.export_csv(path)
            else:
                self.error_occurred.emit(f"Formato desconhecido: {fmt}")
                return
            self.progress_changed.emit(f"Dados exportados para {path}")
        except StorageError as exc:
            self.error_occurred.emit(f"Erro ao exportar: {exc}")
        except OSError as exc:
            self.error_occurred.emit(f"Erro ao salvar arquivo: {exc}")

    # ------------------------------------------------------------------
    # Private slots
    # ------------------------------------------------------------------

    def _on_search_finished(self, result: list) -> None:
        count = len(result)
        msg = (
            f"{count} categoria(s) e subcategoria(s) encontradas e salvas."
            if count > 0
            else "Nenhuma categoria encontrada. Tente um termo diferente."
        )
        self.progress_changed.emit(msg)
        self.search_completed.emit(result)
        self._current_worker = None

    def _on_load_finished(self, result: list) -> None:
        self.progress_changed.emit(f"{len(result)} categoria(s) raiz carregada(s).")
        self.load_completed.emit(result)
        self._current_worker = None

    def _on_refresh_finished(self, result: list) -> None:
        self.progress_changed.emit(
            f"Atualização concluída — {len(result)} categoria(s) no banco."
        )
        self.load_completed.emit(result)
        self._current_worker = None

    def _on_import_finished(self, result: list) -> None:
        count = len(result)
        self.progress_changed.emit(
            f"✅ Importação concluída — {count:,} categorias e subcategorias salvas!"
        )
        self.import_finished.emit(count)
        self.load_completed.emit(result)
        self._current_worker = None

    def _on_error(self, message: str) -> None:
        self.error_occurred.emit(message)
        self._current_worker = None

    def _get_full_tree_from_cache(self, seed_categories: list[CategoryDTO]) -> list[CategoryDTO]:
        """Reconstrói a árvore completa do cache para as categorias encontradas."""
        visited: set[str] = set()
        all_nodes: list[CategoryDTO] = []
        for cat in seed_categories:
            all_nodes.extend(_bfs_from_cache(self._repo, cat.id, visited))
        return all_nodes
