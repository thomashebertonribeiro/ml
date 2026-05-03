# Plano de Implementação: Mercado Livre Category Browser

## Visão Geral

Implementação incremental de uma aplicação desktop PyQt6 para explorar a árvore de categorias do Mercado Livre Brasil. A construção segue a ordem: estrutura do projeto → camada de dados → camada de serviços → camada de aplicação → interface gráfica → integração final.

## Tarefas

- [x] 1. Configurar estrutura do projeto e dependências
  - Criar estrutura de diretórios: `src/`, `src/models/`, `src/services/`, `src/repository/`, `src/ui/`, `tests/`
  - Criar `requirements.txt` com dependências fixadas: `PyQt6==6.7.*`, `requests==2.32.*`, `hypothesis==6.*`, `pytest==8.*`, `pytest-qt==4.*`
  - Criar `src/__init__.py`, `src/models/__init__.py`, `src/services/__init__.py`, `src/repository/__init__.py`, `src/ui/__init__.py`
  - Criar `main.py` como ponto de entrada mínimo (apenas `if __name__ == "__main__": pass`)
  - _Requisitos: 5.1, 7.1_

- [x] 2. Implementar modelos de dados (DTOs)
  - [x] 2.1 Criar `src/models/category.py` com `CategoryDTO` e `CategoryDetailDTO`
    - Implementar dataclasses conforme o design: campos `id`, `name`, `parent_id`, `level`, `total_items_in_this_category`, `path_from_root`, `children_ids`, `updated_at`
    - Implementar `CategoryDetailDTO` estendendo `CategoryDTO` com `picture`, `permalink`, `settings`
    - _Requisitos: 4.1, 2.3_

  - [ ]* 2.2 Escrever teste de propriedade para round-trip de serialização JSON
    - **Propriedade 2: Round-trip de serialização JSON**
    - **Valida: Requisito 4.1**
    - Usar `hypothesis` com `st.lists(st.fixed_dictionaries({"id": st.text(), "name": st.text()}))`
    - Tag: `# Feature: mercadolivre-category-browser, Property 2: serialização round-trip`

- [x] 3. Implementar camada de persistência (DatabaseManager e CategoryRepository)
  - [x] 3.1 Criar `src/repository/database.py` com `DatabaseManager`
    - Implementar `__init__(self, db_path: str)`, `initialize()`, `get_connection()`, `close()`
    - Criar tabelas `categories` e `app_config` com todos os índices definidos no schema
    - Usar `~/.mercadolivre-browser/categories.db` como caminho padrão
    - _Requisitos: 7.1, 4.6_

  - [x] 3.2 Criar `src/repository/category_repository.py` com `CategoryRepository`
    - Implementar `upsert()`, `get_by_id()`, `get_children()`, `get_all()`, `is_stale()`, `search_local()`
    - Implementar `export_json()` e `export_csv()` para exportação de dados
    - Garantir deduplicação via `INSERT OR REPLACE` (upsert) no SQLite
    - _Requisitos: 4.1, 4.2, 4.3, 4.4, 4.6_

  - [ ]* 3.3 Escrever teste de propriedade para unicidade no repositório (upsert idempotente)
    - **Propriedade 1: Unicidade de categorias no repositório**
    - **Valida: Requisito 4.6**
    - Usar banco SQLite em memória (`:memory:`); chamar `upsert` duas vezes com mesmo `category_id`
    - Tag: `# Feature: mercadolivre-category-browser, Property 1: upsert idempotência`

  - [ ]* 3.4 Escrever teste de propriedade para detecção de dados obsoletos
    - **Propriedade 3: Detecção de dados obsoletos (staleness)**
    - **Valida: Requisito 4.3**
    - Usar `st.floats(min_value=0, max_value=72)` para `hours_ago`; verificar `is_stale()` retorna `True` quando `hours_ago > 24`
    - Tag: `# Feature: mercadolivre-category-browser, Property 3: staleness detection`

  - [ ]* 3.5 Escrever teste de propriedade para consistência hierárquica pai-filho
    - **Propriedade 6: Consistência hierárquica pai-filho**
    - **Valida: Requisitos 2.2, 4.1**
    - Inserir lista de categorias com `parent_id`; verificar que `get_children(parent_id)` retorna apenas filhos corretos
    - Tag: `# Feature: mercadolivre-category-browser, Property 6: hierarquia pai-filho`

  - [ ]* 3.6 Escrever testes unitários para `CategoryRepository`
    - Testar `get_by_id` com id inexistente (retorna `None`)
    - Testar `get_children(None)` retorna apenas categorias raiz
    - Testar `search_local` com correspondência parcial de nome (case-insensitive)
    - _Requisitos: 4.1, 4.2_

- [x] 4. Checkpoint — Verificar camada de persistência
  - Garantir que todos os testes da camada de repositório passam. Perguntar ao usuário se há dúvidas antes de continuar.

- [x] 5. Implementar hierarquia de exceções e validação de entrada
  - [x] 5.1 Criar `src/services/exceptions.py` com `AppError`, `ApiError`, `ApiRateLimitError`, `ApiNetworkError`, `StorageError`, `ValidationError`
    - Implementar conforme hierarquia definida no design
    - _Requisitos: 6.1, 6.2, 6.3_

  - [x] 5.2 Criar `src/services/validation.py` com `validate_search_query(query: str) -> None`
    - Levantar `ValidationError` para strings vazias ou compostas apenas de espaços em branco
    - _Requisitos: 1.4_

  - [ ]* 5.3 Escrever teste de propriedade para rejeição de busca vazia
    - **Propriedade 4: Validação de busca vazia**
    - **Valida: Requisito 1.4**
    - Usar `st.text(alphabet=st.characters(whitelist_categories=["Zs", "Cc"]))` com `assume(query.strip() == "")`
    - Tag: `# Feature: mercadolivre-category-browser, Property 4: validação busca vazia`

- [x] 6. Implementar `MercadoLivreClient` com política de retry
  - [x] 6.1 Criar `src/services/ml_client.py` com `MercadoLivreClient`
    - Implementar `get_root_categories()`, `search_categories()`, `get_category_detail()`
    - Configurar `requests.Session` com `HTTPAdapter` e `urllib3.util.retry.Retry`: máximo 3 tentativas, backoff exponencial (2s, 4s, 8s), retry em erros de rede e HTTP 5xx
    - Tratar HTTP 429 respeitando cabeçalho `Retry-After` (fallback: 60s); levantar `ApiRateLimitError`
    - Tratar HTTP 4xx (exceto 429) levantando `ApiError` sem retry
    - _Requisitos: 1.1, 1.3, 2.5, 6.1, 6.2_

  - [x] 6.2 Criar `src/services/retry.py` com função auxiliar `compute_backoff_delay(attempt: int) -> int`
    - Retornar `2 ** attempt` para `attempt` em `{1, 2, 3}`
    - _Requisitos: 6.2_

  - [ ]* 6.3 Escrever teste de propriedade para política de retry com backoff exponencial
    - **Propriedade 5: Política de retry com backoff exponencial**
    - **Valida: Requisito 6.2**
    - Usar `st.integers(min_value=1, max_value=3)`; verificar `compute_backoff_delay(attempt) == 2 ** attempt`
    - Tag: `# Feature: mercadolivre-category-browser, Property 5: retry backoff`

  - [ ]* 6.4 Escrever testes unitários para `MercadoLivreClient`
    - Mockar `requests.Session`; verificar URLs corretas para cada método
    - Testar parsing de resposta JSON para `CategoryDTO` e `CategoryDetailDTO`
    - Testar que HTTP 429 levanta `ApiRateLimitError` com `retry_after` correto
    - Testar que HTTP 404 levanta `ApiError` sem retry
    - _Requisitos: 1.1, 1.5, 6.1_

- [x] 7. Implementar `AppSettings` e configuração de logging
  - [x] 7.1 Criar `src/services/settings.py` com `AppSettings`
    - Implementar `save_window_state()`, `restore_window_state()`, `get()`, `set()` usando `QSettings`
    - _Requisitos: 7.3_

  - [x] 7.2 Criar `src/services/logger.py` com função `setup_logging() -> logging.Logger`
    - Configurar `RotatingFileHandler` com arquivo `~/.mercadolivre-browser/app.log`, tamanho máximo 10 MB, 2 backups
    - Formato: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
    - _Requisitos: 6.4, 6.5_

- [x] 8. Implementar `ApiWorker` e `CategoryController`
  - [x] 8.1 Criar `src/services/worker.py` com `ApiWorker(QRunnable)`
    - Implementar classe interna `Signals(QObject)` com signals `finished`, `error`, `progress`
    - Implementar `run()` executando a task callable e emitindo signals de resultado ou erro
    - _Requisitos: 3.1, 3.5_

  - [x] 8.2 Criar `src/services/controller.py` com `CategoryController(QObject)`
    - Implementar signals: `search_completed`, `load_completed`, `error_occurred`, `progress_changed`
    - Implementar `search(query)`: validar entrada, verificar cache no repositório, submeter `ApiWorker` ao `QThreadPool` se necessário
    - Implementar `load_root_categories()`: verificar cache, submeter worker para buscar da API
    - Implementar `cancel_current_operation()`: cancelar worker em andamento
    - Implementar `export_data(path, fmt)`: delegar ao repositório
    - _Requisitos: 1.1, 1.2, 1.3, 1.4, 2.5, 3.1, 3.3, 3.5, 4.2, 4.3_

  - [ ]* 8.3 Escrever testes unitários para `CategoryController`
    - Mockar `MercadoLivreClient` e `CategoryRepository`
    - Testar que busca com cache válido não chama a API
    - Testar que busca com cache expirado chama a API e persiste resultados
    - Testar que `cancel_current_operation()` interrompe worker em andamento
    - _Requisitos: 3.5, 4.2, 4.3_

- [x] 9. Checkpoint — Verificar camada de serviços
  - Garantir que todos os testes das camadas de serviços e controller passam. Perguntar ao usuário se há dúvidas antes de continuar.

- [x] 10. Implementar interface gráfica — widgets principais
  - [x] 10.1 Criar `src/ui/category_tree_widget.py` com `CategoryTreeWidget(QTreeWidget)`
    - Implementar signal `category_selected = pyqtSignal(str)`
    - Implementar `populate(categories)`, `expand_node(category_id)`, `clear_tree()`
    - Indicar visualmente nós folha (sem ícone de expansão) quando `children_ids` estiver vazio
    - _Requisitos: 2.1, 2.2, 2.4_

  - [x] 10.2 Criar `src/ui/detail_panel.py` com `DetailPanel(QWidget)`
    - Exibir campos: nome, id, total de itens e caminho completo (`path_from_root`) da categoria selecionada
    - _Requisitos: 2.3_

  - [x] 10.3 Criar `src/ui/search_bar.py` com `SearchBar(QWidget)`
    - Implementar campo de texto + botão "Buscar" + botão "Carregar Categorias Raiz"
    - Conectar tecla Enter ao slot de busca
    - Desabilitar campo durante operações em andamento
    - _Requisitos: 1.1, 2.5, 3.3, 5.4_

  - [ ]* 10.4 Escrever testes de UI com `pytest-qt` para widgets principais
    - Testar que `MainWindow` inicializa com dimensões mínimas ≥ 900×600 pixels
    - Testar que Enter no `SearchBar` emite o signal de busca
    - Testar que `StatusBar` exibe mensagens de erro corretamente
    - _Requisitos: 5.3, 5.4_

- [x] 11. Implementar `MainWindow` e integração dos componentes
  - [x] 11.1 Criar `src/ui/main_window.py` com `MainWindow(QMainWindow)`
    - Implementar `_setup_ui()`: compor `SearchBar`, `CategoryTreeWidget`, `DetailPanel`, `QStatusBar`, botão de exportação em layout `QSplitter`
    - Implementar `_connect_signals()`: conectar signals do `CategoryController` aos slots dos widgets
    - Implementar `_restore_state()` e `_save_state()` usando `AppSettings`
    - Implementar `closeEvent()` para salvar estado e fechar conexão com banco
    - Definir dimensões mínimas de 900×600 pixels
    - Respeitar tema do sistema operacional via `QApplication.style()`
    - _Requisitos: 5.1, 5.2, 5.3, 5.5, 5.6, 7.2, 7.3_

  - [x] 11.2 Conectar `CategoryController` à `MainWindow`
    - Instanciar `DatabaseManager`, `CategoryRepository`, `MercadoLivreClient` e `CategoryController` em `MainWindow.__init__`
    - Conectar `search_completed` → `CategoryTreeWidget.populate`
    - Conectar `load_completed` → `CategoryTreeWidget.populate`
    - Conectar `error_occurred` → `QStatusBar.showMessage`
    - Conectar `progress_changed` → `QStatusBar.showMessage`
    - Ao iniciar, chamar `controller.load_root_categories()` para exibir dados do cache local
    - _Requisitos: 3.2, 3.4, 7.2_

  - [x] 11.3 Implementar diálogo de exportação (`ExportDialog`)
    - Criar `src/ui/export_dialog.py` com `QFileDialog` para escolha de caminho e formato (JSON/CSV)
    - Conectar ao `controller.export_data(path, fmt)`
    - _Requisitos: 4.4_

- [x] 12. Implementar `main.py` — ponto de entrada da aplicação
  - Chamar `setup_logging()` antes de criar `QApplication`
  - Instanciar `QApplication`, `MainWindow`, chamar `app.exec()`
  - Tratar `StorageError` na inicialização: exibir `QMessageBox` de aviso e continuar com banco vazio
  - _Requisitos: 7.1, 7.4, 7.5_

- [x] 13. Implementar exportação completa e teste de propriedade de round-trip
  - [x] 13.1 Verificar e completar implementação de `export_json()` e `export_csv()` em `CategoryRepository`
    - Garantir que todos os campos (`id`, `name`, `parent_id`, `level`) são incluídos na exportação
    - _Requisitos: 4.4_

  - [ ]* 13.2 Escrever teste de propriedade para exportação fiel (round-trip)
    - **Propriedade 7: Exportação completa e fiel**
    - **Valida: Requisito 4.4**
    - Inserir lista de categorias no repositório; exportar para JSON; verificar que `exported_ids == original_ids`
    - Tag: `# Feature: mercadolivre-category-browser, Property 7: exportação round-trip`

- [x] 14. Checkpoint final — Garantir que todos os testes passam
  - Executar `pytest tests/` e verificar que todos os testes (unitários, de propriedade e de UI) passam sem erros.
  - Perguntar ao usuário se há ajustes finais antes de considerar a implementação concluída.

## Notas

- Tarefas marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido
- Cada tarefa referencia requisitos específicos para rastreabilidade
- Os checkpoints nas tarefas 4, 9 e 14 garantem validação incremental
- Os testes de propriedade usam a biblioteca `hypothesis` e validam invariantes universais do sistema
- Os testes unitários validam comportamentos específicos e casos de borda
- O banco SQLite é sempre criado em `~/.mercadolivre-browser/categories.db`; testes usam `:memory:` ou `tmp_path`
