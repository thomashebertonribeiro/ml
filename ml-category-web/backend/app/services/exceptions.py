"""
Hierarquia de exceções da aplicação ML Category Web.

As classes AppError e suas subclasses são usadas pelos serviços e routers
para sinalizar condições de erro que o error handler global converte em
respostas HTTP padronizadas.

As classes ApiError, ApiRateLimitError e ApiNetworkError são reutilizadas
do sistema desktop sem dependência de PyQt6.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class AppError(Exception):
    """Base para todas as exceções da aplicação."""

    status_code: int = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


# ---------------------------------------------------------------------------
# HTTP 4xx / 5xx específicos
# ---------------------------------------------------------------------------


class AuthError(AppError):
    """Erros de autenticação e autorização (HTTP 401)."""

    status_code = 401


class ConflictError(AppError):
    """Recurso já existe, ex.: e-mail duplicado ou job em execução (HTTP 409)."""

    status_code = 409


class NotFoundError(AppError):
    """Recurso não encontrado (HTTP 404)."""

    status_code = 404


class ValidationError(AppError):
    """Dados de entrada inválidos (HTTP 422)."""

    status_code = 422


class RateLimitError(AppError):
    """Rate limit excedido (HTTP 429)."""

    status_code = 429

    def __init__(self, message: str, retry_after: int = 60) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ServiceUnavailableError(AppError):
    """Serviço externo ou banco indisponível (HTTP 503)."""

    status_code = 503


# ---------------------------------------------------------------------------
# Reutilizados do sistema desktop (sem dependência PyQt6)
# ---------------------------------------------------------------------------


class ApiError(AppError):
    """Erro retornado pela API do Mercado Livre (HTTP 4xx/5xx)."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        # status_code here refers to the upstream HTTP status, not our own
        super().__init__(message)
        if status_code is not None:
            self.status_code = status_code


class ApiRateLimitError(ApiError):
    """HTTP 429 da API do Mercado Livre — limite de requisições atingido."""

    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(
            f"Limite de requisições atingido. Aguardando {retry_after}s para nova tentativa.",
            status_code=429,
        )
        self.retry_after = retry_after


class ApiNetworkError(AppError):
    """Falha de rede (timeout, conexão recusada, sem internet)."""
