"""
Import router.

Endpoints (all require authentication):
    POST /import/start    — enqueue a manual import job (HTTP 202)
    GET  /import/status   — get the most recent import job status (HTTP 200)
    GET  /import/progress — SSE stream of live import progress (HTTP 200)
"""

from __future__ import annotations

import json

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.import_job import ImportJob
from app.models.user import User
from app.schemas.import_job import ImportStartResponse, ImportStatusOut
from app.services.exceptions import ConflictError, NotFoundError
from app.workers.import_task import import_categories

router = APIRouter(prefix="/import", tags=["import"])


# ---------------------------------------------------------------------------
# POST /import/start
# ---------------------------------------------------------------------------


@router.post(
    "/start",
    response_model=ImportStartResponse,
    status_code=202,
    summary="Start a manual import job",
)
async def start_import(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ImportStartResponse:
    """Enqueue a Celery task to import all ML categories.

    Raises:
        ConflictError (HTTP 409): if an import job is already running.
    """
    # Check for an already-running job
    result = await db.execute(
        select(ImportJob).where(ImportJob.status == "running").limit(1)
    )
    running_job = result.scalar_one_or_none()

    if running_job is not None:
        raise ConflictError("Uma importação já está em andamento.")

    # Enqueue the Celery task
    task = import_categories.delay(triggered_by="manual")

    return ImportStartResponse(job_id=str(task.id), status="pending")


# ---------------------------------------------------------------------------
# GET /import/status
# ---------------------------------------------------------------------------


@router.get(
    "/status",
    response_model=ImportStatusOut,
    status_code=200,
    summary="Get the most recent import job status",
)
async def get_import_status(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> ImportStatusOut:
    """Return the most recent import job.

    Raises:
        NotFoundError (HTTP 404): if no import job exists.
    """
    result = await db.execute(
        select(ImportJob).order_by(ImportJob.created_at.desc()).limit(1)
    )
    job = result.scalar_one_or_none()

    if job is None:
        raise NotFoundError("Nenhuma importação encontrada.")

    return ImportStatusOut(
        job_id=str(job.id),
        status=job.status,  # type: ignore[arg-type]
        processed=job.processed,
        total_estimated=job.total_estimated,
        started_at=job.started_at,
        finished_at=job.finished_at,
        error_count=job.error_count,
    )


# ---------------------------------------------------------------------------
# GET /import/progress
# ---------------------------------------------------------------------------


@router.get(
    "/progress",
    status_code=200,
    summary="SSE stream of live import progress",
)
async def get_import_progress(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Stream real-time import progress events via Server-Sent Events.

    Raises:
        NotFoundError (HTTP 404): if no import job is currently running.
    """
    # Verify there is a running job and capture its ID
    result = await db.execute(
        select(ImportJob).where(ImportJob.status == "running").limit(1)
    )
    running_job = result.scalar_one_or_none()

    if running_job is None:
        raise NotFoundError("Não há importação em andamento.")

    job_id = str(running_job.id)

    async def _event_generator():
        redis_client: aioredis.Redis = aioredis.Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        try:
            pubsub = redis_client.pubsub()
            channel = f"import:progress:{job_id}"
            await pubsub.subscribe(channel)

            async for raw_message in pubsub.listen():
                # Skip subscription confirmation messages
                if raw_message["type"] != "message":
                    continue

                data: str = raw_message["data"]
                yield f"data: {data}\n\n"

                # Stop streaming when the job reaches a terminal state
                try:
                    event = json.loads(data)
                    if event.get("status") in ("completed", "failed"):
                        break
                except (json.JSONDecodeError, AttributeError):
                    pass
        finally:
            await redis_client.aclose()

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
