#!/bin/bash
# Script de execução do Mercado Livre Category Browser
# Usa o Python 3.13 que tem PyQt6 instalado

PYTHON="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13"

if [ ! -f "$PYTHON" ]; then
    echo "Erro: Python 3.13 não encontrado em $PYTHON"
    echo "Tente instalar o PyQt6 no Python padrão:"
    echo "  python3 -m pip install PyQt6 requests"
    exit 1
fi

cd "$(dirname "$0")"
exec "$PYTHON" main.py "$@"
