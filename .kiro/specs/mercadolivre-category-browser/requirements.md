# Documento de Requisitos

## Introdução

O **Mercado Livre Category Browser** é uma aplicação desktop desenvolvida com PyQt6 que permite ao usuário explorar a árvore de categorias e subcategorias do Mercado Livre Brasil (site MLB). O sistema consome a API REST pública do Mercado Livre (`https://api.mercadolibre.com`) para buscar categorias por nome ou navegar pela hierarquia completa, exibindo os resultados em uma interface gráfica intuitiva. Todas as categorias e subcategorias encontradas são persistidas localmente em um banco de dados SQLite para consulta offline e histórico.

A abordagem técnica adotada é a **API oficial do Mercado Livre**, que disponibiliza endpoints públicos de leitura sem necessidade de autenticação para navegação na árvore de categorias:
- `GET /sites/MLB/categories` — lista as categorias raiz do Brasil
- `GET /categories/{category_id}` — retorna detalhes e subcategorias filhas (`children_categories`)
- `GET /sites/MLB/domain_discovery/search?q={termo}` — preditor de categoria por texto livre

---

## Glossário

- **Application**: A aplicação desktop PyQt6 como um todo.
- **API_Client**: O módulo responsável por realizar requisições HTTP à API REST do Mercado Livre.
- **Category_Browser**: O componente de interface gráfica principal que exibe a árvore de categorias.
- **Category**: Uma categoria do Mercado Livre, identificada por um `id` (ex.: `MLB1051`) e um `name` (ex.: `Celulares e Telefones`).
- **Subcategory**: Uma categoria filha de outra categoria, retornada no campo `children_categories` da API.
- **Category_Tree**: A estrutura hierárquica completa de categorias e subcategorias de um site do Mercado Livre.
- **Local_Storage**: O banco de dados SQLite local onde categorias e subcategorias são persistidas.
- **Search_Bar**: O campo de texto da interface onde o usuário digita o termo de busca.
- **Result_Panel**: O painel da interface que exibe a árvore de resultados de categorias e subcategorias.
- **Status_Bar**: A barra de status da interface que exibe mensagens de progresso e erros.
- **MLB**: Identificador do site Mercado Livre Brasil (`https://api.mercadolibre.com/sites/MLB`).
- **Root_Category**: Uma categoria de nível superior, sem categoria pai, retornada pelo endpoint `/sites/MLB/categories`.
- **Leaf_Category**: Uma categoria sem subcategorias filhas (`children_categories` vazio).

---

## Requisitos

### Requisito 1: Busca de Categorias por Nome

**User Story:** Como usuário, quero digitar o nome de uma categoria no campo de busca, para que o sistema encontre e exiba as categorias correspondentes no Mercado Livre Brasil.

#### Critérios de Aceitação

1. WHEN o usuário digita um termo no Search_Bar e aciona a busca, THE Application SHALL consultar o endpoint `GET /sites/MLB/domain_discovery/search?q={termo}` da API do Mercado Livre para identificar categorias correspondentes.
2. WHEN a busca retorna resultados, THE Result_Panel SHALL exibir cada categoria encontrada com seu nome e identificador (id).
3. WHEN a busca retorna resultados, THE Application SHALL buscar automaticamente as subcategorias de cada categoria encontrada via `GET /categories/{category_id}`.
4. WHEN o termo de busca está vazio, THE Application SHALL exibir uma mensagem de validação no Status_Bar informando que o campo de busca não pode estar vazio.
5. IF a API retornar um erro HTTP (4xx ou 5xx), THEN THE Status_Bar SHALL exibir uma mensagem de erro descritiva contendo o código HTTP e uma orientação ao usuário.
6. IF a conexão com a API falhar por timeout ou ausência de rede, THEN THE Application SHALL exibir uma mensagem de erro no Status_Bar e manter os dados previamente carregados no Result_Panel.

---

### Requisito 2: Navegação pela Árvore de Categorias

**User Story:** Como usuário, quero visualizar a hierarquia completa de categorias e subcategorias, para que eu possa explorar a estrutura do Mercado Livre de forma organizada.

#### Critérios de Aceitação

1. THE Category_Browser SHALL exibir as categorias e suas subcategorias em uma estrutura de árvore hierárquica expansível e recolhível.
2. WHEN o usuário expande um nó de categoria no Category_Browser, THE Application SHALL exibir todas as subcategorias filhas daquela categoria.
3. WHEN o usuário seleciona uma categoria no Category_Browser, THE Result_Panel SHALL exibir as informações detalhadas da categoria selecionada, incluindo: nome, id, número total de itens e caminho completo desde a raiz (`path_from_root`).
4. WHEN uma categoria não possui subcategorias (Leaf_Category), THE Category_Browser SHALL indicar visualmente que o nó é uma folha, sem ícone de expansão.
5. THE Application SHALL permitir carregar todas as Root_Categories do MLB via botão dedicado na interface, consultando `GET /sites/MLB/categories`.

---

### Requisito 3: Carregamento Assíncrono e Feedback de Progresso

**User Story:** Como usuário, quero que o sistema busque dados sem travar a interface gráfica, para que eu possa continuar interagindo com a aplicação durante o carregamento.

#### Critérios de Aceitação

1. WHEN uma busca ou carregamento de categorias é iniciado, THE Application SHALL executar a requisição à API em uma thread separada, sem bloquear a interface gráfica.
2. WHILE uma requisição à API está em andamento, THE Status_Bar SHALL exibir um indicador de progresso (spinner ou mensagem de "Carregando...").
3. WHILE uma requisição à API está em andamento, THE Search_Bar SHALL ser desabilitado para evitar buscas simultâneas.
4. WHEN o carregamento é concluído com sucesso, THE Status_Bar SHALL exibir o número de categorias e subcategorias encontradas.
5. WHEN o usuário aciona uma nova busca enquanto outra está em andamento, THE Application SHALL cancelar a requisição anterior antes de iniciar a nova.

---

### Requisito 4: Persistência Local de Categorias e Subcategorias

**User Story:** Como usuário, quero que o sistema salve localmente todas as categorias e subcategorias encontradas, para que eu possa consultá-las offline e evitar buscas repetidas.

#### Critérios de Aceitação

1. WHEN uma categoria ou subcategoria é retornada pela API, THE Local_Storage SHALL persistir os dados contendo: id, nome, id da categoria pai (se houver), nível hierárquico e timestamp da última atualização.
2. WHEN o usuário realiza uma busca por um termo já pesquisado anteriormente, THE Application SHALL verificar se os dados existem no Local_Storage antes de consultar a API.
3. WHERE os dados no Local_Storage tiverem mais de 24 horas desde o timestamp de atualização, THE Application SHALL revalidar os dados consultando a API e atualizando o Local_Storage.
4. THE Application SHALL fornecer uma função de exportação que salva todas as categorias e subcategorias armazenadas no Local_Storage em um arquivo JSON ou CSV escolhido pelo usuário.
5. IF a escrita no Local_Storage falhar, THEN THE Application SHALL registrar o erro em um arquivo de log e continuar exibindo os dados obtidos da API na interface.
6. THE Local_Storage SHALL garantir que não existam registros duplicados para o mesmo id de categoria.

---

### Requisito 5: Interface Gráfica com PyQt6

**User Story:** Como usuário, quero uma interface gráfica intuitiva e responsiva, para que eu possa usar o sistema de forma eficiente sem conhecimento técnico.

#### Critérios de Aceitação

1. THE Application SHALL ser implementada utilizando PyQt6 como framework de interface gráfica.
2. THE Application SHALL conter os seguintes elementos na janela principal: Search_Bar com botão de busca, botão para carregar todas as Root_Categories, Result_Panel com árvore hierárquica, painel de detalhes da categoria selecionada, Status_Bar e botão de exportação.
3. THE Application SHALL ter uma janela principal com dimensões mínimas de 900x600 pixels, redimensionável pelo usuário.
4. WHEN o usuário pressiona a tecla Enter no Search_Bar, THE Application SHALL acionar a busca, equivalente ao clique no botão de busca.
5. THE Application SHALL suportar redimensionamento da janela principal mantendo o layout proporcional dos painéis.
6. WHERE o sistema operacional suportar temas escuro e claro, THE Application SHALL respeitar a preferência de tema do sistema operacional.

---

### Requisito 6: Tratamento de Erros e Resiliência

**User Story:** Como usuário, quero que o sistema trate erros de forma clara e continue funcionando, para que eu não perca dados ou precise reiniciar a aplicação em caso de falhas.

#### Critérios de Aceitação

1. IF a API do Mercado Livre retornar o código HTTP 429 (rate limit), THEN THE API_Client SHALL aguardar o tempo indicado no cabeçalho `Retry-After` (ou 60 segundos como padrão) antes de realizar uma nova tentativa automática.
2. THE API_Client SHALL realizar no máximo 3 tentativas automáticas para requisições que falhem com erros de rede transitórios (timeout, conexão recusada), com intervalo exponencial de 2, 4 e 8 segundos entre tentativas.
3. IF todas as tentativas de requisição falharem, THEN THE Application SHALL exibir no Status_Bar uma mensagem de erro clara indicando a causa da falha e sugerindo verificar a conexão com a internet.
4. THE Application SHALL registrar todos os erros em um arquivo de log local (`app.log`) com timestamp, tipo de erro e contexto da operação.
5. IF o arquivo de log ultrapassar 10 MB, THEN THE Application SHALL realizar rotação do arquivo de log, mantendo os 2 arquivos de log mais recentes.

---

### Requisito 7: Configuração e Inicialização

**User Story:** Como usuário, quero que a aplicação inicialize rapidamente e mantenha minhas configurações entre sessões, para que eu possa retomar o trabalho de onde parei.

#### Critérios de Aceitação

1. WHEN a Application é iniciada pela primeira vez, THE Application SHALL criar automaticamente o banco de dados Local_Storage e o arquivo de configuração no diretório de dados do usuário.
2. WHEN a Application é iniciada, THE Application SHALL carregar e exibir no Category_Browser as categorias previamente salvas no Local_Storage, sem necessidade de nova consulta à API.
3. THE Application SHALL salvar o estado da janela (posição, tamanho e estado dos painéis) ao ser fechada e restaurar esse estado na próxima inicialização.
4. THE Application SHALL inicializar e exibir a janela principal em no máximo 3 segundos em hardware convencional (processador dual-core, 4 GB RAM, SSD).
5. IF o Local_Storage estiver corrompido ou inacessível na inicialização, THEN THE Application SHALL exibir uma mensagem de aviso ao usuário e inicializar com o banco de dados vazio, sem encerrar a aplicação.
