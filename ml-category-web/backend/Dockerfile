# Stage base
FROM python:3.12-slim AS base
WORKDIR /app
RUN pip install --no-cache-dir --upgrade pip
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Stage development
FROM base AS development
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage production
FROM base AS production
COPY . .
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4"]
