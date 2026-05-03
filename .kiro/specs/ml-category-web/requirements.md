# Documento de Requisitos

## Introdução

O **ML Category Web** é uma aplicação web full-stack que substitui e expande o sistema desktop de exploração de categorias do Mercado Livre Brasil (MLB). O sistema permite que múltiplos usuários autenticados pesquisem, naveguem e exportem a árvore hierárquica de categorias do MLB via navegador web, com importação em background via Celery, progresso em tempo real via SSE, atualização automática agendada e uma API REST pública para integração com sistemas externos.

A aplicação é composta por:
- **Backend**: FastAPI (Python) expondo uma API REST e endpoints SSE
- **Frontend**: React (SPA) consumindo a API e exibindo a interface
- **Banco de dados**: PostgreSQL para persistência de categorias, usuários e histórico
- **Fila de tarefas**: Celery + Redis para importação assíncrona e agendamento

O sistema consome a API REST pública do Mercado Livre (`https://api.mercadolibre.com`):
- `GET /sites/MLB/categories` — lista as 31 categorias raiz do Brasil
- `GET /categories/{category_id}` — retorna detalhes e subcategorias filhas
- `GET /sites/MLB/domain_discovery/search?q={termo}` — preditor de categoria por texto livre

---

## Glossário

- **System**: A aplicação web ML Category Web como um todo (backend + frontend).
- **API**: O backend FastAPI que expõe endpoints REST e SSE.
- **Frontend**: A Single Page Application React servida ao navegador do usuário.
- **ML_Client**: O módulo Python responsável por realizar requisições HTTP à API pública do Mercado Livre.
- **Category**: Uma categoria do Mercado Livre, identificada por um `id` (ex.: `MLB1051`) e um `name` (ex.: `Celulares e Telefones`).
- **Subcategory**: Uma categoria filha de outra categoria, retornada no campo `children_categories` da API do ML.
- **Category_Tree**: A estrutura hierárquica completa de categorias e subcategorias do MLB.
- **Root_Category**: Uma categoria de nível superior sem categoria pai, retornada por `GET /sites/MLB/categories`.
- **Leaf_Category**: Uma categoria sem subcategorias filhas (`children_categories` vazio).
- **Database**: O banco de dados PostgreSQL onde categorias, usuários, histórico e configurações são persistidos.
- **Import_Job**: Uma tarefa Celery responsável por buscar recursivamente toda a Category_Tree do MLB e persistir no Database.
- **Scheduler**: O Celery Beat responsável por agendar execuções periódicas do Import_Job.
- **SSE_Stream**: Um endpoint Server-Sent Events que transmite eventos de progresso do Import_Job ao Frontend em tempo real.
- **User**: Um usuário autenticado do sistema, identificado por e-mail e senha.
- **Auth_Token**: Um JSON Web Token (JWT) emitido pelo API após autenticação bem-sucedida do User.
- **Change_Log**: O registro histórico de adições e remoções de subcategorias detectadas entre execuções do Import_Job.
- **Dashboard**: A página do Frontend que exibe estatísticas agregadas sobre as categorias importadas.
- **Public_API**: O conjunto de endpoints REST do API acessíveis sem autenticação para consulta de categorias por sistemas externos.
- **Export_File**: Um arquivo JSON ou CSV gerado pelo API contendo categorias exportadas para download.
- **Cache**: Camada de cache em Redis utilizada pelo API para respostas de consultas frequentes.
- **MLB**: Identificador do site Mercado Livre Brasil (`https://api.mercadolibre.com/sites/MLB`).

---

## Requisitos

### Requisito 1: Autenticação de Usuários

**User Story:** Como usuário, quero me registrar e fazer login na aplicação web, para que eu possa acessar as funcionalidades de forma segura e personalizada.

#### Critérios de Aceitação

1. THE API SHALL fornecer um endpoint `POST /auth/register` que aceita e-mail e senha, cria um novo User no Database e retorna um Auth_Token JWT com validade de 24 horas.
2. THE API SHALL fornecer um endpoint `POST /auth/login` que aceita e-mail e senha, valida as credenciais contra o Database e retorna um Auth_Token JWT com validade de 24 horas.
3. WHEN o User fornece uma senha no registro, THE API SHALL armazenar no Database apenas o hash bcrypt da senha, nunca o valor em texto plano.
4. IF o User fornece credenciais inválidas no login, THEN THE API SHALL retornar HTTP 401 com uma mensagem de erro genérica que não revele se o e-mail ou a senha está incorreto.
5. IF o User tenta registrar um e-mail já cadastrado, THEN THE API SHALL retornar HTTP 409 com uma mensagem indicando que o e-mail já está em uso.
6. WHEN o Frontend recebe um Auth_Token, THE Frontend SHALL armazenar o token em memória (não em localStorage) e incluí-lo no cabeçalho `Authorization: Bearer {token}` em todas as requisições autenticadas subsequentes.
7. IF uma requisição autenticada chegar ao API com um Auth_Token expirado ou inválido, THEN THE API SHALL retornar HTTP 401 e THE Frontend SHALL redirecionar o User para a página de login.
8. THE API SHALL fornecer um endpoint `POST /auth/refresh` que aceita um Auth_Token válido e retorna um novo Auth_Token com validade renovada de 24 horas.

---

### Requisito 2: Busca de Categorias por Nome

**User Story:** Como usuário autenticado, quero buscar categorias do MLB por nome via interface web, para que eu possa encontrar rapidamente a categoria desejada sem navegar pela árvore completa.

#### Critérios de Aceitação

1. THE API SHALL fornecer um endpoint `GET /categories/search?q={termo}` que consulta o Database por categorias cujo nome contenha o termo fornecido, com busca case-insensitive.
2. WHEN o termo de busca corresponder a categorias no Database, THE API SHALL retornar uma lista de categorias contendo: id, nome, nível hierárquico, id da categoria pai e caminho completo desde a raiz.
3. WHEN o usuário digita um termo no campo de busca do Frontend e aciona a busca, THE Frontend SHALL exibir os resultados em uma lista hierárquica com no máximo 50 itens por página.
4. IF o termo de busca tiver menos de 2 caracteres, THEN THE API SHALL retornar HTTP 422 com uma mensagem de validação indicando o mínimo de caracteres exigido.
5. IF nenhuma categoria for encontrada para o termo buscado, THEN THE API SHALL retornar HTTP 200 com uma lista vazia e THE Frontend SHALL exibir uma mensagem informando que nenhuma categoria foi encontrada.
6. THE API SHALL armazenar em Cache os resultados de buscas por até 5 minutos, retornando a resposta em cache para termos idênticos dentro desse período.
7. WHEN o usuário seleciona uma categoria nos resultados de busca, THE Frontend SHALL exibir o painel de detalhes da categoria contendo: id, nome, nível, total de itens, caminho desde a raiz e lista de subcategorias diretas.

---

### Requisito 3: Navegação pela Árvore Hierárquica de Categorias

**User Story:** Como usuário autenticado, quero visualizar e navegar pela árvore hierárquica completa de categorias do MLB, para que eu possa explorar a estrutura de categorias de forma organizada.

#### Critérios de Aceitação

1. THE API SHALL fornecer um endpoint `GET /categories` que retorna todas as Root_Categories armazenadas no Database.
2. THE API SHALL fornecer um endpoint `GET /categories/{category_id}/children` que retorna as subcategorias diretas de uma categoria específica armazenadas no Database.
3. THE API SHALL fornecer um endpoint `GET /categories/{category_id}` que retorna os detalhes completos de uma categoria específica armazenada no Database.
4. THE Frontend SHALL exibir as Root_Categories em uma árvore hierárquica expansível, carregando as subcategorias de cada nó sob demanda ao expandir o nó (lazy loading).
5. WHEN o usuário expande um nó na árvore, THE Frontend SHALL exibir as subcategorias filhas daquele nó, obtidas via `GET /categories/{category_id}/children`.
6. WHEN uma categoria é uma Leaf_Category, THE Frontend SHALL indicar visualmente que o nó não possui filhos, sem exibir ícone de expansão.
7. WHEN o usuário seleciona um nó na árvore, THE Frontend SHALL exibir o painel de detalhes da categoria selecionada contendo: id, nome, nível hierárquico, total de itens, caminho desde a raiz e lista de subcategorias diretas.
8. IF o Database não contiver categorias importadas, THEN THE Frontend SHALL exibir uma mensagem orientando o usuário a iniciar a importação.

---

### Requisito 4: Importação de Categorias em Background

**User Story:** Como usuário autenticado, quero importar todas as categorias do MLB em background, para que a interface permaneça responsiva durante o processo de importação.

#### Critérios de Aceitação

1. THE API SHALL fornecer um endpoint `POST /import/start` que enfileira um Import_Job no Celery e retorna imediatamente um `job_id` com HTTP 202.
2. WHEN o Import_Job é executado, THE Import_Job SHALL buscar recursivamente toda a Category_Tree do MLB a partir das 31 Root_Categories via ML_Client e persistir cada categoria no Database.
3. WHEN o Import_Job encontra uma categoria já existente no Database, THE Import_Job SHALL atualizar os dados da categoria existente (upsert) sem criar duplicatas.
4. WHEN o Import_Job detecta que uma subcategoria presente no Database não existe mais na API do ML, THE Import_Job SHALL registrar a remoção no Change_Log com timestamp e dados da categoria removida.
5. WHEN o Import_Job detecta uma nova subcategoria que não existia no Database, THE Import_Job SHALL registrar a adição no Change_Log com timestamp e dados da categoria adicionada.
6. IF um Import_Job já estiver em execução, THEN THE API SHALL retornar HTTP 409 ao receber uma nova requisição `POST /import/start`, indicando que uma importação já está em andamento.
7. THE API SHALL fornecer um endpoint `GET /import/status` que retorna o status atual do Import_Job mais recente: estado (pending, running, completed, failed), total de categorias processadas, total estimado e timestamp de início.
8. IF o ML_Client falhar ao buscar uma categoria durante o Import_Job, THEN THE Import_Job SHALL registrar o erro, incrementar um contador de falhas e continuar processando as demais categorias sem interromper o job.

---

### Requisito 5: Progresso em Tempo Real via SSE

**User Story:** Como usuário autenticado, quero acompanhar o progresso da importação em tempo real na interface web, para que eu saiba quantas categorias já foram importadas sem precisar atualizar a página.

#### Critérios de Aceitação

1. THE API SHALL fornecer um endpoint `GET /import/progress` que estabelece uma conexão SSE e transmite eventos de progresso enquanto um Import_Job estiver em execução.
2. WHEN o Import_Job processa uma categoria, THE API SHALL emitir um evento SSE contendo: número de categorias processadas, total estimado, percentual de conclusão e nome da categoria sendo processada no momento.
3. WHEN o Import_Job é concluído com sucesso, THE API SHALL emitir um evento SSE final com status `completed`, total de categorias importadas e duração total da importação, e encerrar a conexão SSE.
4. IF o Import_Job falhar, THEN THE API SHALL emitir um evento SSE com status `failed` e mensagem de erro descritiva, e encerrar a conexão SSE.
5. THE Frontend SHALL exibir uma barra de progresso e contador de categorias processadas, atualizados em tempo real a partir dos eventos SSE recebidos.
6. WHEN a conexão SSE for interrompida pelo cliente (usuário fecha a aba ou navega para outra página), THE API SHALL encerrar o stream SSE sem afetar a execução do Import_Job em background.
7. IF o Frontend tentar se conectar ao endpoint SSE sem um Import_Job em execução, THEN THE API SHALL retornar HTTP 404 indicando que não há importação em andamento.

---

### Requisito 6: Atualização Automática Agendada

**User Story:** Como administrador, quero que o sistema atualize automaticamente as categorias do MLB em intervalos regulares, para que os dados permaneçam atualizados sem intervenção manual.

#### Critérios de Aceitação

1. THE Scheduler SHALL executar automaticamente um Import_Job a cada 24 horas para atualizar todas as categorias do MLB no Database.
2. WHEN o Scheduler inicia um Import_Job agendado, THE Import_Job SHALL seguir o mesmo processo de importação definido no Requisito 4, incluindo detecção de mudanças e registro no Change_Log.
3. THE API SHALL fornecer um endpoint `GET /scheduler/status` que retorna: status do Scheduler (ativo/inativo), timestamp da última execução agendada, timestamp da próxima execução agendada e resultado da última execução.
4. IF o Import_Job agendado falhar, THEN THE Scheduler SHALL registrar a falha no log do sistema e tentar novamente na próxima janela de agendamento, sem interromper o ciclo de agendamento.
5. WHERE o administrador desejar configurar o intervalo de atualização, THE API SHALL fornecer um endpoint `PUT /scheduler/config` que aceita um intervalo em horas (mínimo 1 hora, máximo 168 horas) e atualiza a configuração do Scheduler.

---

### Requisito 7: Exportação de Categorias

**User Story:** Como usuário autenticado, quero exportar as categorias importadas para JSON ou CSV, para que eu possa utilizar os dados em outros sistemas ou análises.

#### Critérios de Aceitação

1. THE API SHALL fornecer um endpoint `GET /export?format={json|csv}` que gera e retorna um Export_File contendo todas as categorias armazenadas no Database com os campos: id, nome, id da categoria pai, nível hierárquico, total de itens e caminho desde a raiz.
2. WHEN o formato solicitado for `json`, THE API SHALL retornar o Export_File com `Content-Type: application/json` e `Content-Disposition: attachment; filename="ml_categories_{timestamp}.json"`.
3. WHEN o formato solicitado for `csv`, THE API SHALL retornar o Export_File com `Content-Type: text/csv` e `Content-Disposition: attachment; filename="ml_categories_{timestamp}.csv"`, com cabeçalho de colunas na primeira linha.
4. IF o formato solicitado não for `json` nem `csv`, THEN THE API SHALL retornar HTTP 422 com uma mensagem indicando os formatos suportados.
5. THE Frontend SHALL fornecer botões de exportação para JSON e CSV que acionam o download do Export_File diretamente no navegador do usuário.
6. WHERE o usuário desejar exportar apenas uma subárvore, THE API SHALL aceitar um parâmetro opcional `root_id={category_id}` no endpoint de exportação e retornar apenas as categorias pertencentes àquela subárvore.
7. IF o Database não contiver categorias, THEN THE API SHALL retornar HTTP 404 com uma mensagem indicando que não há dados para exportar.

---

### Requisito 8: Histórico de Mudanças

**User Story:** Como usuário autenticado, quero visualizar o histórico de mudanças nas categorias do MLB, para que eu possa acompanhar quando subcategorias foram adicionadas ou removidas ao longo do tempo.

#### Critérios de Aceitação

1. THE API SHALL fornecer um endpoint `GET /changes` que retorna os registros do Change_Log em ordem cronológica decrescente, com paginação de 50 itens por página.
2. WHEN um registro do Change_Log é retornado, THE API SHALL incluir os campos: id do registro, tipo de mudança (`added` ou `removed`), id da categoria afetada, nome da categoria afetada, id da categoria pai, timestamp da detecção e id do Import_Job que detectou a mudança.
3. THE API SHALL aceitar parâmetros de filtro no endpoint `GET /changes`: `type` (added/removed), `category_id`, `from_date` e `to_date` para restringir os resultados.
4. THE Frontend SHALL exibir o histórico de mudanças em uma tabela paginada com colunas: data, tipo de mudança, categoria afetada e categoria pai.
5. WHEN o usuário filtra o histórico por tipo de mudança no Frontend, THE Frontend SHALL atualizar a tabela exibindo apenas os registros do tipo selecionado.
6. THE API SHALL fornecer um endpoint `GET /changes/summary` que retorna um resumo agregado: total de adições e remoções por mês nos últimos 12 meses.

---

### Requisito 9: Dashboard com Estatísticas

**User Story:** Como usuário autenticado, quero visualizar um dashboard com estatísticas sobre as categorias importadas, para que eu tenha uma visão geral do estado atual dos dados.

#### Critérios de Aceitação

1. THE API SHALL fornecer um endpoint `GET /dashboard/stats` que retorna as seguintes métricas: total de categorias importadas, total de Root_Categories, total de Leaf_Categories, profundidade máxima da árvore, timestamp da última importação e total de mudanças detectadas nos últimos 30 dias.
2. THE Frontend SHALL exibir as métricas do dashboard em cards visuais na página inicial após o login do usuário.
3. WHEN o usuário acessa o Dashboard, THE Frontend SHALL buscar as métricas via `GET /dashboard/stats` e exibir os dados atualizados.
4. THE API SHALL armazenar em Cache os resultados de `GET /dashboard/stats` por até 5 minutos para reduzir a carga no Database.
5. THE Frontend SHALL exibir no Dashboard um gráfico de barras com o número de categorias por nível hierárquico (nível 0, 1, 2, 3 e demais).
6. THE Frontend SHALL exibir no Dashboard o status da última importação (data, duração, total importado) e um botão para iniciar uma nova importação manual.

---

### Requisito 10: API REST Pública para Consulta de Categorias

**User Story:** Como desenvolvedor externo, quero consultar as categorias do MLB via API REST sem autenticação, para que eu possa integrar os dados de categorias em meus próprios sistemas.

#### Critérios de Aceitação

1. THE Public_API SHALL fornecer o endpoint `GET /public/categories` que retorna todas as Root_Categories sem exigir Auth_Token.
2. THE Public_API SHALL fornecer o endpoint `GET /public/categories/{category_id}` que retorna os detalhes de uma categoria específica sem exigir Auth_Token.
3. THE Public_API SHALL fornecer o endpoint `GET /public/categories/{category_id}/children` que retorna as subcategorias diretas de uma categoria sem exigir Auth_Token.
4. THE Public_API SHALL fornecer o endpoint `GET /public/categories/search?q={termo}` que busca categorias por nome sem exigir Auth_Token, com os mesmos critérios de validação do Requisito 2.
5. THE API SHALL aplicar rate limiting de 60 requisições por minuto por endereço IP nos endpoints da Public_API.
6. IF o rate limit for excedido, THEN THE API SHALL retornar HTTP 429 com o cabeçalho `Retry-After` indicando o número de segundos até a próxima janela disponível.
7. THE Public_API SHALL retornar respostas no formato JSON com o cabeçalho `Content-Type: application/json` e incluir o cabeçalho `X-Total-Count` com o total de itens disponíveis em endpoints de listagem.
8. THE API SHALL armazenar em Cache os resultados dos endpoints da Public_API por até 5 minutos para reduzir a carga no Database.

---

### Requisito 11: Resiliência e Tratamento de Erros

**User Story:** Como usuário, quero que o sistema trate erros de forma clara e continue funcionando, para que eu não perca dados ou precise reiniciar a aplicação em caso de falhas.

#### Critérios de Aceitação

1. IF a API do Mercado Livre retornar HTTP 429 durante o Import_Job, THEN THE ML_Client SHALL aguardar o tempo indicado no cabeçalho `Retry-After` (ou 60 segundos como padrão) antes de realizar uma nova tentativa automática.
2. THE ML_Client SHALL realizar no máximo 3 tentativas automáticas para requisições que falhem com erros de rede transitórios (timeout, conexão recusada), com intervalo exponencial de 2, 4 e 8 segundos entre tentativas.
3. IF todas as tentativas de uma requisição ao ML_Client falharem, THEN THE Import_Job SHALL registrar o erro no log do sistema, incrementar o contador de falhas do job e continuar processando as demais categorias.
4. THE API SHALL retornar respostas de erro no formato JSON padronizado contendo os campos: `error` (código de erro), `message` (descrição legível) e `timestamp` para todos os erros HTTP 4xx e 5xx.
5. THE API SHALL registrar todos os erros internos (HTTP 5xx) no log do sistema com nível ERROR, incluindo stack trace, endpoint afetado e timestamp.
6. IF o Database estiver inacessível, THEN THE API SHALL retornar HTTP 503 com uma mensagem indicando indisponibilidade temporária do serviço.
7. IF o Redis estiver inacessível, THEN THE API SHALL continuar operando sem Cache, retornando respostas diretamente do Database, e registrar um aviso no log do sistema.

---

### Requisito 12: Desempenho e Escalabilidade

**User Story:** Como usuário, quero que a aplicação responda rapidamente às minhas consultas, para que eu possa trabalhar de forma eficiente mesmo com grandes volumes de dados.

#### Critérios de Aceitação

1. THE API SHALL responder a requisições de busca e listagem de categorias em no máximo 500ms para 95% das requisições, medido no servidor, com o Database contendo até 100.000 categorias.
2. THE Database SHALL manter índices nas colunas `parent_id`, `name` e `level` da tabela de categorias para garantir desempenho nas consultas mais frequentes.
3. THE API SHALL suportar no mínimo 100 requisições simultâneas sem degradação de desempenho acima do limite de 500ms definido no critério 1.
4. THE Import_Job SHALL processar no mínimo 10 categorias por segundo durante a importação, medido como média ao longo de toda a execução do job.
5. THE API SHALL implementar paginação em todos os endpoints de listagem que possam retornar mais de 50 itens, utilizando os parâmetros `page` e `page_size` (máximo de 100 itens por página).
6. WHERE o resultado de uma consulta estiver disponível em Cache, THE API SHALL retornar a resposta em Cache em no máximo 50ms.
