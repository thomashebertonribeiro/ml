# Plano de Implementação: ML Category Web

## Visão Geral

Implementação incremental do sistema web de categorias do Mercado Livre Brasil. A construção segue a ordem: infraestrutura → backend core → Celery workers → routers API → frontend → deploy na VPS.

## Tarefas

- [x] 1. Configurar estrutura do projeto e infraestrutura base
  - [x] 1.1 Criar estrutura de diretórios do monorepo
    - Criar `ml-category-web/backend/`, `ml-category-web/frontend/`, `ml-category-web/nginx/`
    - Criar `backend/app/` com subpastas: `models/`, `schemas/`, `routers/`, `services/`, `workers/`
    - Criar `backend/alembic/versions/` e `backend/tests/properties/`
    - _Requisitos: todos_

  - [x] 1.2 Criar `backend/pyproject.toml` com dependências fixadas
    - Dependências: `fastapi==0.111.*`, `uvicorn[standard]==0.30.*`, `sqlalchemy[asyncio]==2.0.*`, `alembic==1.13.*`, `asyncpg==0.29.*`, `pydantic[email]==2.7.*`, `pydantic-settings==2.3.*`, `python-jose[cryptography]==3.3.*`, `passlib[bcrypt]==1.7.*`, `celery[redis]==5.4.*`, `redis==5.0.*`, `httpx==0.27.*`, `structlog==24.*`, `hypothesis==6.*`, `pytest==8.*`, `pytest-asyncio==0.23.*`
    - _Requisitos: todos_

  - [x] 1.3 Criar `backend/app/config.py` com Settings via pydantic-settings
    - Campos: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `ENVIRONMENT`, `ACCESS_TOKEN_EXPIRE_SECONDS=86400`, `RATE_LIMIT_PER_MINUTE=60`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
    - Carregar de variáveis de ambiente e arquivo `.env`
    - _Requisitos: todos_

  - [x] 1.4 Criar `backend/app/database.py` com engine async SQLAlchemy
    - Criar `async_engine` com `create_async_engine(DATABASE_URL)`
    - Criar `AsyncSessionLocal` com `async_sessionmaker`
    - Criar `Base = DeclarativeBase()`
    - Criar dependência `get_db()` para FastAPI
    - _Requisitos: todos_

  - [x] 1.5 Criar `docker-compose.yml` com todos os serviços
    - Serviços: `db` (postgres:16-alpine), `redis` (redis:7-alpine), `backend`, `celery_worker`, `celery_beat`, `frontend`
    - Healthchecks para `db` e `redis`
    - Variáveis de ambiente via `.env`
    - _Requisitos: todos_

  - [x] 1.6 Criar `backend/.env.example` e `docker-compose.prod.yml`
    - `.env.example` com todas as variáveis necessárias documentadas
    - `docker-compose.prod.yml` sobrepondo configurações de produção (workers=4, restart=unless-stopped, Nginx, Certbot)
    - _Requisitos: todos_

- [x] 2. Implementar modelos ORM e migration inicial
  - [x] 2.1 Criar `backend/app/models/user.py` com modelo `User`
    - Campos: `id` (UUID), `email` (unique), `password_hash`, `created_at`, `updated_at`
    - _Requisitos: 1.1, 1.2, 1.3_

  - [x] 2.2 Criar `backend/app/models/category.py` com modelo `Category`
    - Campos: `id` (TEXT PK), `name`, `parent_id` (FK self-referencial), `level`, `total_items`, `path_json` (JSONB), `updated_at`
    - Relacionamentos: `children`, `parent`
    - _Requisitos: 3.1, 3.2, 3.3_

  - [x] 2.3 Criar `backend/app/models/import_job.py` com modelo `ImportJob`
    - Campos: `id` (UUID), `status` (pending/running/completed/failed), `processed`, `total_estimated`, `error_count`, `started_at`, `finished_at`, `triggered_by`, `created_at`
    - _Requisitos: 4.1, 4.7_

  - [x] 2.4 Criar `backend/app/models/change_log.py` com modelo `ChangeLog`
    - Campos: `id` (BIGSERIAL), `change_type` (added/removed), `category_id`, `category_name`, `parent_id`, `detected_at`, `import_job_id` (FK)
    - _Requisitos: 4.4, 4.5, 8.1, 8.2_

  - [x] 2.5 Criar `backend/app/models/scheduler_config.py` com modelo `SchedulerConfig`
    - Campos: `id=1` (singleton), `interval_hours`, `active`, `last_run_at`, `next_run_at`, `last_run_result`, `updated_at`
    - _Requisitos: 6.1, 6.3, 6.5_

  - [x] 2.6 Configurar Alembic e criar migration inicial
    - Configurar `alembic/env.py` para usar `async_engine` e importar todos os modelos
    - Criar `alembic/versions/0001_initial_schema.py` com todas as tabelas, índices e extensões (`pgcrypto`, `pg_trgm`)
    - Incluir seed da tabela `scheduler_config` (INSERT id=1)
    - _Requisitos: 12.2_

- [x] 3. Implementar schemas Pydantic e hierarquia de exceções
  - [x] 3.1 Criar `backend/app/schemas/auth.py`
    - `RegisterRequest`, `LoginRequest`, `TokenResponse`, `RefreshRequest`
    - _Requisitos: 1.1, 1.2, 1.8_

  - [x] 3.2 Criar `backend/app/schemas/category.py`
    - `PathNode`, `CategoryOut`, `CategoryDetail`, `SearchResponse`
    - _Requisitos: 2.2, 3.2, 3.3_

  - [x] 3.3 Criar `backend/app/schemas/import_job.py`
    - `ImportStartResponse`, `ImportStatusOut`, `SSEProgressEvent`
    - _Requisitos: 4.1, 4.7, 5.2_

  - [x] 3.4 Criar `backend/app/schemas/change_log.py`, `dashboard.py`, `scheduler.py`
    - `ChangeLogOut`, `ChangeSummaryItem`, `DashboardStats`, `SchedulerStatus`, `SchedulerConfigUpdate`
    - _Requisitos: 8.1, 8.2, 9.1, 6.3, 6.5_

  - [x] 3.5 Criar `backend/app/services/exceptions.py` com hierarquia completa
    - `AppError`, `AuthError`, `ConflictError`, `NotFoundError`, `ValidationError`, `RateLimitError`, `ServiceUnavailableError`
    - Reutilizar `ApiError`, `ApiRateLimitError`, `ApiNetworkError` do sistema desktop
    - _Requisitos: 11.4, 11.5_

- [x] 4. Implementar autenticação JWT
  - [x] 4.1 Criar `backend/app/services/auth_service.py`
    - `hash_password(password) -> str` — bcrypt hash
    - `verify_password(plain, hashed) -> bool` — bcrypt verify
    - `create_access_token(user_id, email) -> str` — JWT com exp 24h
    - `decode_token(token) -> dict` — valida e decodifica JWT
    - _Requisitos: 1.1, 1.2, 1.3, 1.4_

  - [x] 4.2 Criar `backend/app/dependencies.py` com dependências FastAPI
    - `get_db()` — sessão async SQLAlchemy
    - `get_current_user(token)` — valida JWT e retorna User; levanta AuthError se inválido
    - `get_redis()` — conexão Redis
    - _Requisitos: 1.7_

  - [x] 4.3 Criar `backend/app/routers/auth.py`
    - `POST /auth/register` — cria usuário, retorna TokenResponse (HTTP 201)
    - `POST /auth/login` — valida credenciais, retorna TokenResponse (HTTP 200)
    - `POST /auth/refresh` — renova token (HTTP 200)
    - Tratar: e-mail duplicado (409), credenciais inválidas (401)
    - _Requisitos: 1.1, 1.2, 1.4, 1.5, 1.7, 1.8_

  - [ ]* 4.4 Escrever testes de propriedade para autenticação
    - **Propriedade 1: Round-trip registro → login**
    - **Propriedade 2: Rejeição de tokens inválidos**
    - Tag: `# Feature: ml-category-web, Property 1: register then login round-trip`
    - _Requisitos: 1.1, 1.2, 1.3, 1.7_

- [x] 5. Implementar serviço de categorias e routers
  - [x] 5.1 Criar `backend/app/services/category_service.py`
    - `get_root_categories(db) -> list[Category]`
    - `get_category_by_id(db, id) -> Category | None`
    - `get_children(db, parent_id) -> list[Category]`
    - `search_categories(db, query, page, page_size) -> tuple[list[Category], int]`
    - `upsert_category(db, data) -> Category` — INSERT OR UPDATE idempotente
    - _Requisitos: 3.1, 3.2, 3.3, 2.1, 2.6_

  - [x] 5.2 Criar `backend/app/services/cache_service.py`
    - `get_cached(redis, key) -> dict | None`
    - `set_cached(redis, key, value, ttl_seconds=300)`
    - `invalidate(redis, pattern)`
    - _Requisitos: 2.6, 9.4, 10.8, 11.7_

  - [x] 5.3 Criar `backend/app/routers/categories.py`
    - `GET /categories` — lista Root_Categories (com cache 5min)
    - `GET /categories/search?q=&page=&page_size=` — busca (valida min 2 chars)
    - `GET /categories/{id}` — detalhes com filhos
    - `GET /categories/{id}/children` — filhos diretos
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [ ]* 5.4 Escrever testes de propriedade para busca e consistência
    - **Propriedade 3: Corretude da busca**
    - **Propriedade 4: Rejeição de termo curto**
    - **Propriedade 5: Paginação nunca excede limite**
    - **Propriedade 6: Invariante de categorias raiz**
    - **Propriedade 7: Consistência pai-filho**
    - **Propriedade 8: Round-trip de persistência**
    - **Propriedade 9: Idempotência do upsert**
    - Tag: `# Feature: ml-category-web, Property 3: search correctness`
    - _Requisitos: 2.1, 2.4, 3.1, 3.2, 3.3, 4.3, 12.5_

- [x] 6. Implementar Celery worker e tarefa de importação
  - [x] 6.1 Criar `backend/app/workers/celery_app.py`
    - Configurar `Celery` com broker Redis e result backend Redis
    - Configurar `beat_schedule` para `import_categories` a cada 24h
    - _Requisitos: 6.1, 6.2_

  - [x] 6.2 Criar `backend/app/workers/ml_client.py`
    - Adaptar `MercadoLivreClient` do sistema desktop para uso no worker Celery
    - Remover dependências PyQt6 (já inexistentes no módulo de serviços)
    - Manter `fetch_full_tree` com BFS, retry exponencial e delay configurável
    - _Requisitos: 11.1, 11.2, 11.3_

  - [x] 6.3 Criar `backend/app/workers/import_task.py` com `@celery.task import_categories`
    - Verificar se já existe job em execução (evitar duplicatas)
    - Criar registro `ImportJob` com status `running`
    - Buscar árvore completa via `fetch_full_tree` para cada Root_Category
    - Fazer upsert de cada categoria via `category_service.upsert_category`
    - Detectar adições/remoções comparando com estado anterior no banco
    - Registrar mudanças no `ChangeLog`
    - Publicar eventos de progresso no Redis (canal `import:progress:{job_id}`)
    - Atualizar `ImportJob` com status `completed` ou `failed`
    - _Requisitos: 4.2, 4.3, 4.4, 4.5, 4.6, 4.8, 11.1, 11.2, 11.3_

  - [ ]* 6.4 Escrever testes de propriedade para importação
    - **Propriedade 10: Completude da importação**
    - **Propriedade 11: Detecção de mudanças no Change_Log**
    - **Propriedade 12: Resiliência a falhas parciais**
    - **Propriedade 22: Backoff exponencial**
    - Tag: `# Feature: ml-category-web, Property 10: import completeness`
    - _Requisitos: 4.2, 4.4, 4.5, 4.8, 11.2_

- [x] 7. Implementar routers de importação e SSE
  - [x] 7.1 Criar `backend/app/routers/import_router.py`
    - `POST /import/start` — enfileira `import_categories`, retorna 202 com `job_id`; retorna 409 se já em execução
    - `GET /import/status` — retorna `ImportStatusOut` do job mais recente
    - `GET /import/progress` — endpoint SSE: lê eventos do Redis e transmite ao cliente; retorna 404 se não há job em execução
    - _Requisitos: 4.1, 4.6, 4.7, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [ ]* 7.2 Escrever testes de propriedade para SSE
    - **Propriedade 13: Completude dos eventos SSE**
    - Tag: `# Feature: ml-category-web, Property 13: SSE progress events`
    - _Requisitos: 5.2_

- [x] 8. Implementar routers de exportação, histórico e dashboard
  - [x] 8.1 Criar `backend/app/services/export_service.py`
    - `export_json(db, root_id=None) -> str` — serializa categorias para JSON
    - `export_csv(db, root_id=None) -> str` — serializa categorias para CSV
    - Suporte a filtro por subárvore via `root_id`
    - _Requisitos: 7.1, 7.2, 7.3, 7.6_

  - [x] 8.2 Criar `backend/app/routers/export.py`
    - `GET /export?format=json|csv&root_id=` — retorna `StreamingResponse` com headers corretos
    - Validar formato (422 se inválido); 404 se banco vazio
    - _Requisitos: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

  - [x] 8.3 Criar `backend/app/routers/changes.py`
    - `GET /changes?type=&category_id=&from_date=&to_date=&page=&page_size=` — lista Change_Log paginado
    - `GET /changes/summary` — agregado por mês dos últimos 12 meses
    - _Requisitos: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [x] 8.4 Criar `backend/app/routers/dashboard.py`
    - `GET /dashboard/stats` — retorna `DashboardStats` (com cache Redis 5min)
    - _Requisitos: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [ ]* 8.5 Escrever testes de propriedade para exportação e histórico
    - **Propriedade 14: Completude da exportação**
    - **Propriedade 15: Exportação de subárvore**
    - **Propriedade 16: Validação de formato**
    - **Propriedade 17: Ordenação do Change_Log**
    - **Propriedade 18: Corretude dos filtros**
    - **Propriedade 19: Consistência das estatísticas**
    - Tag: `# Feature: ml-category-web, Property 14: export completeness`
    - _Requisitos: 7.1, 7.4, 7.6, 8.1, 8.3, 9.1_

- [x] 9. Implementar API pública, scheduler e rate limiting
  - [x] 9.1 Criar `backend/app/services/rate_limiter.py`
    - Sliding window counter no Redis por IP
    - `check_rate_limit(redis, ip, limit=60, window=60) -> bool`
    - Retornar `Retry-After` quando excedido
    - _Requisitos: 10.5, 10.6_

  - [x] 9.2 Criar `backend/app/routers/public.py`
    - `GET /public/categories` — Root_Categories sem auth (com cache 5min)
    - `GET /public/categories/{id}` — detalhes sem auth
    - `GET /public/categories/{id}/children` — filhos sem auth
    - `GET /public/categories/search?q=` — busca sem auth
    - Aplicar rate limiting (60 req/min/IP) em todos os endpoints
    - Incluir header `X-Total-Count` em listagens
    - _Requisitos: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_

  - [x] 9.3 Criar `backend/app/routers/scheduler.py`
    - `GET /scheduler/status` — retorna `SchedulerStatus`
    - `PUT /scheduler/config` — atualiza `interval_hours` (1-168h)
    - _Requisitos: 6.3, 6.4, 6.5_

  - [ ]* 9.4 Escrever testes de propriedade para rate limiting e API pública
    - **Propriedade 20: Rate limiting da Public API**
    - **Propriedade 21: Cabeçalho X-Total-Count**
    - Tag: `# Feature: ml-category-web, Property 20: rate limiting`
    - _Requisitos: 10.5, 10.6, 10.7_

- [x] 10. Configurar FastAPI app factory, middleware e handler de erros
  - [x] 10.1 Criar `backend/app/main.py` com app factory
    - Registrar todos os routers com prefixos corretos
    - Configurar CORS (origens permitidas via settings)
    - Configurar middleware de logging estruturado (structlog)
    - Registrar handler global de erros (`AppError` → JSON padronizado)
    - Registrar handler para erros não tratados (HTTP 500 com log ERROR)
    - _Requisitos: 11.4, 11.5, 11.6, 11.7_

  - [x] 10.2 Criar `backend/Dockerfile` multi-stage
    - Stage `base`: Python 3.12-slim, instala dependências
    - Stage `development`: com reload
    - Stage `production`: sem reload, com `alembic upgrade head` no entrypoint
    - _Requisitos: todos_

- [x] 11. Checkpoint backend — verificar que todos os testes passam
  - Executar `pytest tests/` e verificar que todos os testes (unitários, de propriedade e de integração) passam
  - Verificar que `alembic upgrade head` executa sem erros
  - Verificar que todos os endpoints respondem corretamente via `curl` ou Swagger UI

- [x] 12. Implementar frontend — estrutura base e autenticação
  - [x] 12.1 Criar projeto React com Vite + TypeScript
    - `npm create vite@latest frontend -- --template react-ts`
    - Instalar dependências: `axios`, `@tanstack/react-query`, `zustand`, `react-router-dom`, `recharts`
    - Configurar `vite.config.ts` com proxy para API em desenvolvimento
    - _Requisitos: todos_

  - [x] 12.2 Criar `frontend/src/api/client.ts`
    - Instância Axios com `baseURL` configurável via `VITE_API_URL`
    - Interceptor de request: adiciona `Authorization: Bearer {token}` do `authStore`
    - Interceptor de response: redireciona para `/login` em HTTP 401
    - _Requisitos: 1.6, 1.7_

  - [x] 12.3 Criar `frontend/src/store/authStore.ts` com Zustand
    - Estado: `token` (em memória, NUNCA localStorage), `isAuthenticated`
    - Actions: `setToken`, `clearToken`
    - _Requisitos: 1.6_

  - [x] 12.4 Criar `LoginPage.tsx`, `RegisterPage.tsx` e `ProtectedRoute.tsx`
    - Formulários com validação client-side (e-mail, senha mínimo 8 chars)
    - `ProtectedRoute` redireciona para `/login` se não autenticado
    - _Requisitos: 1.1, 1.2, 1.6, 1.7_

- [x] 13. Implementar frontend — navegação de categorias e busca
  - [x] 13.1 Criar `frontend/src/hooks/useCategories.ts`
    - React Query hooks: `useRootCategories`, `useCategoryChildren`, `useCategoryDetail`, `useSearchCategories`
    - Cache automático de nós já expandidos
    - _Requisitos: 3.4, 3.5, 3.7_

  - [x] 13.2 Criar `CategoryTree.tsx` e `CategoryNode.tsx`
    - Árvore hierárquica com lazy loading (carrega filhos ao expandir)
    - Indicação visual de nós folha (sem ícone de expansão)
    - Emite `onSelect(category)` ao selecionar um nó
    - _Requisitos: 3.4, 3.5, 3.6, 3.7, 3.8_

  - [x] 13.3 Criar `CategoryDetail.tsx` e `SearchBar.tsx`
    - `CategoryDetail`: exibe id, nome, nível, total de itens, caminho, filhos diretos
    - `SearchBar`: campo com debounce 300ms, mínimo 2 chars, exibe resultados em lista
    - _Requisitos: 2.3, 2.5, 2.7, 3.7_

  - [x] 13.4 Criar `BrowsePage.tsx` e `SearchPage.tsx`
    - `BrowsePage`: layout com `CategoryTree` à esquerda e `CategoryDetail` à direita
    - `SearchPage`: `SearchBar` + lista de resultados paginada
    - Mensagem quando banco está vazio (orientar a importar)
    - _Requisitos: 3.8_

- [x] 14. Implementar frontend — importação, dashboard e histórico
  - [x] 14.1 Criar `frontend/src/hooks/useSSE.ts`
    - Encapsula `EventSource` com token JWT via fetch polyfill
    - Cleanup automático no unmount
    - Retorna `{ data, error, connected }`
    - _Requisitos: 5.5_

  - [x] 14.2 Criar `frontend/src/store/importStore.ts` e `ImportProgress.tsx`
    - `importStore`: estado da importação (processed, total, percent, status)
    - `ImportProgress`: barra de progresso + contador atualizado via SSE
    - Fecha conexão SSE ao receber `completed` ou `failed`
    - _Requisitos: 5.5, 5.6_

  - [x] 14.3 Criar `DashboardPage.tsx` com `StatsCards.tsx` e `LevelChart.tsx`
    - `StatsCards`: cards com total de categorias, raízes, folhas, profundidade máxima, última importação
    - `LevelChart`: gráfico de barras (Recharts) com categorias por nível hierárquico
    - Botão "Iniciar Importação" que abre `ImportProgress`
    - _Requisitos: 9.2, 9.3, 9.5, 9.6_

  - [x] 14.4 Criar `ChangesPage.tsx` com `ChangeLogTable.tsx`
    - Tabela paginada com colunas: data, tipo (added/removed), categoria, categoria pai
    - Filtros por tipo de mudança
    - _Requisitos: 8.4, 8.5_

  - [x] 14.5 Criar `Navbar.tsx` e `App.tsx` com React Router
    - Rotas: `/login`, `/register`, `/` (dashboard), `/browse`, `/search`, `/changes`
    - Navbar com links e botão de logout
    - `ErrorBoundary` global
    - _Requisitos: todos_

  - [x] 14.6 Criar `frontend/Dockerfile` multi-stage
    - Stage `development`: `npm run dev`
    - Stage `production`: `npm run build` + Nginx para servir arquivos estáticos
    - _Requisitos: todos_

- [x] 15. Configurar Nginx e deploy na VPS
  - [x] 15.1 Criar `nginx/nginx.conf` completo
    - Redirect HTTP → HTTPS
    - Proxy `/api/` → FastAPI com `proxy_buffering off` para SSE
    - Servir React SPA com `try_files $uri /index.html`
    - SSL TLS 1.2/1.3, HSTS, headers de segurança
    - _Requisitos: todos_

  - [x] 15.2 Criar `README.md` com guia de deploy na VPS
    - Pré-requisitos: Docker, Docker Compose, domínio apontando para o IP da VPS
    - Passo a passo: clonar repo, configurar `.env`, obter certificado SSL com Certbot, subir containers
    - Comandos: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
    - Renovação automática do certificado via container Certbot
    - _Requisitos: todos_

  - [x] 15.3 Obter certificado SSL inicial com Certbot
    - Subir Nginx temporariamente na porta 80 para validação ACME
    - Executar `certbot certonly --webroot` para o domínio
    - Reiniciar Nginx com SSL habilitado
    - _Requisitos: todos_

- [x] 16. Checkpoint final — verificar sistema completo
  - Executar `pytest tests/` no backend e verificar que todos os testes passam
  - Executar `npm test` no frontend e verificar que todos os testes passam
  - Verificar que o sistema completo funciona via Docker Compose em ambiente local
  - Verificar que o deploy na VPS está funcional com HTTPS
  - Verificar que o Celery Beat está agendando corretamente

## Notas

- Tarefas marcadas com `*` são opcionais (testes de propriedade) e podem ser puladas para um MVP mais rápido
- O código Python do sistema desktop (`MercadoLivreClient`, `fetch_full_tree`) é reutilizado no worker Celery sem modificações estruturais
- O banco SQLite do sistema desktop é independente — o sistema web usa PostgreSQL separado
- Migrations Alembic devem ser executadas antes de subir o backend: `alembic upgrade head`
- Em produção, usar `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`
- O certificado SSL é obtido uma vez e renovado automaticamente pelo container Certbot a cada 12h
