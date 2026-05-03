# Stage base — instala dependências
FROM python:3.12-slim AS base
WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

# Copia pyproject.toml e instala dependências de produção
COPY pyproject.toml .

# Instala todas as dependências (prod + dev) sem modo editable
RUN pip install --no-cache-dir \
    fastapi==0.111.* \
    "uvicorn[standard]==0.30.*" \
    "sqlalchemy[asyncio]==2.0.*" \
    alembic==1.13.* \
    asyncpg==0.29.* \
    "pydantic[email]==2.7.*" \
    pydantic-settings==2.3.* \
    "python-jose[cryptography]==3.3.*" \
    "passlib[bcrypt]==1.7.*" \
    "celery[redis]==5.4.*" \
    redis==5.0.* \
    httpx==0.27.* \
    structlog==24.* \
    requests==2.32.* \
    urllib3==2.* \
    hypothesis==6.* \
    pytest==8.* \
    pytest-asyncio==0.23.*

# Stage development
FROM base AS development
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage production
FROM base AS production
COPY . .
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4"]
