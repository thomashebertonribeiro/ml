"""
Cliente HTTP para a API REST pública do Mercado Livre Brasil.

Adaptado do sistema desktop (src/services/ml_client.py) para uso no
worker Celery. Diferenças em relação ao original:

- Sem dependências de dataclasses do sistema desktop (CategoryDTO, etc.)
- Retorna ``dict`` simples em vez de dataclasses
- Usa ``app.services.exceptions`` (ApiError, ApiRateLimitError, ApiNetworkError)
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.services.exceptions import ApiError, ApiNetworkError, ApiRateLimitError

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.mercadolibre.com"
_TIMEOUT = 15  # segundos


def _build_session() -> requests.Session:
    """Cria uma Session com política de retry para erros de rede e HTTP 5xx."""
    retry_policy = Retry(
        total=3,
        backoff_factor=1,          # 2s, 4s, 8s (backoff_factor * 2^(n-1))
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_policy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    # User-Agent de browser é necessário — a API do ML bloqueia requests
    # sem User-Agent com HTTP 403
    session.headers.update({
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    })
    return session


class MercadoLivreClient:
    """Realiza chamadas HTTP à API REST pública do Mercado Livre.

    Endpoints utilizados:
    - ``GET /sites/MLB/categories`` — categorias raiz do Brasil
    - ``GET /categories/{category_id}`` — detalhes e subcategorias

    Todos os métodos retornam ``dict`` simples (sem dataclasses).
    """

    BASE_URL = _BASE_URL

    def __init__(self) -> None:
        self._session = _build_session()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_root_categories(self) -> list[dict]:
        """Retorna todas as categorias raiz do Mercado Livre Brasil (MLB).

        Tenta o endpoint ``/sites/MLB/categories``. Se retornar 403
        (bloqueio sem autenticação), usa lista de categorias raiz
        conhecidas do MLB como fallback.

        Returns:
            Lista de dicts com keys: ``id``, ``name``, ``parent_id`` (None),
            ``level`` (0).

        Raises:
            ApiNetworkError: Em caso de falha de rede.
        """
        url = f"{self.BASE_URL}/sites/MLB/categories"
        try:
            data = self._get(url)
            return [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "parent_id": None,
                    "level": 0,
                }
                for item in data
            ]
        except ApiError as exc:
            if exc.status_code == 403:
                logger.warning(
                    "GET /sites/MLB/categories retornou 403 — usando lista de categorias conhecidas."
                )
                return self._get_known_root_categories()
            raise

    # Categorias raiz do MLB conhecidas (fallback quando /sites/MLB/categories retorna 403)
    _KNOWN_ROOT_CATEGORIES = [
        ("MLB5672", "Acessórios para Veículos"),
        ("MLB271599", "Agro"),
        ("MLB1403", "Alimentos e Bebidas"),
        ("MLB1071", "Animais e Mascotas"),
        ("MLB1367", "Antiguidades e Coleções"),
        ("MLB1368", "Arte, Papelaria e Armarinho"),
        ("MLB1384", "Bebês"),
        ("MLB1246", "Beleza e Cuidado Pessoal"),
        ("MLB1132", "Brinquedos e Hobbies"),
        ("MLB1430", "Calçados, Roupas e Bolsas"),
        ("MLB1039", "Câmeras e Acessórios"),
        ("MLB1743", "Casa, Móveis e Decoração"),
        ("MLB1574", "Construção"),
        ("MLB1051", "Celulares e Telefones"),
        ("MLB1500", "Computadores"),
        ("MLB1276", "Eletrodomésticos"),
        ("MLB1000", "Eletrônicos, Áudio e Vídeo"),
        ("MLB1182", "Esportes e Fitness"),
        ("MLB218519", "Ferramentas"),
        ("MLB1144", "Filmes e Séries"),
        ("MLB1499", "Games"),
        ("MLB3937", "Imóveis"),
        ("MLB1459", "Indústria e Comércio"),
        ("MLB1648", "Informática"),
        ("MLB1168", "Instrumentos Musicais"),
        ("MLB1196", "Joias e Relógios"),
        ("MLB1520", "Livros, Revistas e Comics"),
        ("MLB1785", "Música"),
        ("MLB1953", "Saúde"),
        ("MLB1540", "Serviços"),
        ("MLB1234", "Veículos"),
    ]

    def _get_known_root_categories(self) -> list[dict]:
        """Retorna lista hardcoded das categorias raiz do MLB."""
        return [
            {
                "id": cat_id,
                "name": name,
                "parent_id": None,
                "level": 0,
            }
            for cat_id, name in self._KNOWN_ROOT_CATEGORIES
        ]

    def get_category_detail(self, category_id: str) -> dict:
        """Retorna detalhes completos de uma categoria, incluindo subcategorias diretas.

        Args:
            category_id: Identificador da categoria (ex.: ``"MLB1051"``).

        Returns:
            Dict com keys: ``id``, ``name``, ``parent_id``, ``level``,
            ``total_items``, ``path_json``, ``children_ids``.

        Raises:
            ApiError: Em caso de erro HTTP 4xx/5xx.
            ApiNetworkError: Em caso de falha de rede.
        """
        url = f"{self.BASE_URL}/categories/{category_id}"
        data = self._get(url)

        # Determina parent_id e level a partir de path_from_root
        path_from_root = data.get("path_from_root", [])
        if len(path_from_root) >= 2:
            parent_id = path_from_root[-2]["id"]
            level = len(path_from_root) - 1
        else:
            parent_id = None
            level = 0

        children = data.get("children_categories", [])
        children_ids = [c["id"] for c in children]

        return {
            "id": data["id"],
            "name": data["name"],
            "parent_id": parent_id,
            "level": level,
            "total_items": data.get("total_items_in_this_category", 0),
            "path_json": path_from_root,
            "children_ids": children_ids,
        }

    def fetch_full_tree(
        self,
        root_id: str,
        progress_callback=None,
        visited: set | None = None,
        delay_ms: int = 150,
    ) -> list[dict]:
        """Busca recursivamente toda a árvore de subcategorias de *root_id*.

        Usa BFS (breadth-first search) para percorrer a hierarquia.

        Args:
            root_id: ID da categoria raiz a expandir.
            progress_callback: Callable opcional que recebe string de progresso.
            visited: Conjunto de IDs já visitados (evita loops).
            delay_ms: Intervalo em ms entre requisições (padrão: 150ms).

        Returns:
            Lista plana de dicts com todos os nós da árvore.
            Cada dict tem as mesmas keys de :meth:`get_category_detail`.
        """
        if visited is None:
            visited = set()

        result: list[dict] = []
        queue: list[str] = [root_id]

        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            try:
                if progress_callback:
                    progress_callback(f"Buscando {current_id}...")
                detail = self.get_category_detail(current_id)
                result.append(detail)
                for child_id in detail["children_ids"]:
                    if child_id not in visited:
                        queue.append(child_id)
                if delay_ms > 0:
                    time.sleep(delay_ms / 1000.0)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Erro ao buscar categoria %s: %s", current_id, exc)

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, url: str, params: dict | None = None) -> list | dict:
        """Executa GET com tratamento de erros HTTP e de rede.

        Trata HTTP 429 respeitando o cabeçalho ``Retry-After``.
        Levanta :class:`ApiRateLimitError`, :class:`ApiError` ou
        :class:`ApiNetworkError` conforme o caso.
        """
        try:
            response = self._session.get(url, params=params, timeout=_TIMEOUT)
        except requests.exceptions.Timeout as exc:
            raise ApiNetworkError("Timeout ao conectar à API do Mercado Livre.") from exc
        except requests.exceptions.ConnectionError as exc:
            raise ApiNetworkError("Sem conexão com a internet. Verifique sua rede.") from exc
        except requests.exceptions.RequestException as exc:
            raise ApiNetworkError(f"Erro de rede: {exc}") from exc

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            logger.warning("HTTP 429 — aguardando %ds (Retry-After)", retry_after)
            time.sleep(retry_after)
            # Tenta novamente uma única vez após o cooldown
            try:
                response = self._session.get(url, params=params, timeout=_TIMEOUT)
            except requests.exceptions.RequestException as exc:
                raise ApiNetworkError(f"Erro de rede após rate limit: {exc}") from exc
            if response.status_code == 429:
                raise ApiRateLimitError(retry_after=retry_after)

        if response.status_code >= 400:
            raise ApiError(
                f"Erro na requisição (HTTP {response.status_code}).",
                status_code=response.status_code,
            )

        return response.json()
