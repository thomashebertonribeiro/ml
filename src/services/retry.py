"""Utilitários de retry e backoff exponencial."""

from __future__ import annotations


def compute_backoff_delay(attempt: int) -> int:
    """Calcula o intervalo de espera para a tentativa *attempt*.

    Retorna ``2 ** attempt`` segundos:
    - attempt=1 → 2s
    - attempt=2 → 4s
    - attempt=3 → 8s

    Args:
        attempt: Número da tentativa (1-indexado, entre 1 e 3).

    Returns:
        Número de segundos a aguardar antes da próxima tentativa.
    """
    return 2 ** attempt
