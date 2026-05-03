"""Validação de entrada do usuário."""

from __future__ import annotations

from src.services.exceptions import ValidationError


def validate_search_query(query: str) -> None:
    """Valida o termo de busca digitado pelo usuário.

    Levanta :class:`ValidationError` se *query* for vazia ou composta
    apenas de espaços em branco.

    Args:
        query: Termo de busca a ser validado.

    Raises:
        ValidationError: Quando *query* está vazia ou só tem whitespace.
    """
    if not query or not query.strip():
        raise ValidationError("Por favor, digite um termo para buscar.")
