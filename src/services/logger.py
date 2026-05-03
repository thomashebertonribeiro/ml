"""Configuração de logging com rotação automática de arquivos."""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

_LOG_DIR = os.path.expanduser("~/.mercadolivre-browser")
_LOG_FILE = os.path.join(_LOG_DIR, "app.log")
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_BACKUP_COUNT = 2
_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configura o sistema de logging da aplicação.

    Cria um :class:`RotatingFileHandler` em
    ``~/.mercadolivre-browser/app.log`` com rotação a cada 10 MB,
    mantendo 2 arquivos de backup.

    Args:
        level: Nível de logging (padrão: ``logging.INFO``).

    Returns:
        Logger raiz configurado.
    """
    os.makedirs(_LOG_DIR, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Evita adicionar handlers duplicados em re-inicializações
    if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
        file_handler = RotatingFileHandler(
            _LOG_FILE,
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(_FORMAT))
        root_logger.addHandler(file_handler)

    # Handler de console para desenvolvimento
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)
               for h in root_logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(_FORMAT))
        root_logger.addHandler(console_handler)

    return root_logger
