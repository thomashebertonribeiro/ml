"""Hierarquia de exceções da aplicação Mercado Livre Category Browser."""

from __future__ import annotations


class AppError(Exception):
    """Exceção base para todos os erros da aplicação."""


class ApiError(AppError):
    """Erro retornado pela API do Mercado Livre (HTTP 4xx/5xx)."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class ApiRateLimitError(ApiError):
    """HTTP 429 — limite de requisições atingido."""

    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(
            f"Limite de requisições atingido. Aguardando {retry_after}s para nova tentativa.",
            status_code=429,
        )
        self.retry_after = retry_after


class ApiNetworkError(AppError):
    """Falha de rede (timeout, conexão recusada, sem internet)."""


class StorageError(AppError):
    """Erro ao ler ou escrever no banco de dados local."""


class ValidationError(AppError):
    """Erro de validação de entrada do usuário."""
