"""
Celery task para importação completa das categorias do Mercado Livre Brasil.

Fluxo da tarefa:
1. Verifica se já existe job em execução (retorna erro se sim)
2. Cria ImportJob com status 'running'
3. Busca árvore completa via fetch_full_tree para cada categoria raiz
4. Faz upsert de cada categoria no PostgreSQL
5. Detecta adições/remoções comparando com estado anterior
6. Registra mudanças no ChangeLog
7. Publica eventos de progresso no Redis (canal 'import:progress:{job_id}')
8. Atualiza ImportJob com status 'completed' ou 'failed'
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

import redis as redis_sync
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.category import Category
from app.models.change_log import ChangeLog
from app.models.import_job import ImportJob
from app.workers.celery_app import celery_app
from app.workers.ml_client import MercadoLivreClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Async engine dedicado ao worker (não compartilhado com o FastAPI)
# ---------------------------------------------------------------------------

_worker_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

_WorkerSession = async_sessionmaker(
    bind=_worker_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# Helpers async
# ---------------------------------------------------------------------------


async def _get_running_job(session: AsyncSession) -> ImportJob | None:
    """Retorna o job em execução, se houver."""
    result = await session.execute(
        select(ImportJob).where(ImportJob.status == "running").limit(1)
    )
    return result.scalar_one_or_none()


async def _create_job(session: AsyncSession, triggered_by: str) -> ImportJob:
    """Cria e persiste um novo ImportJob com status 'running'."""
    job = ImportJob(
        id=uuid4(),
        status="running",
        triggered_by=triggered_by,
        started_at=datetime.now(timezone.utc),
        processed=0,
        total_estimated=0,
        error_count=0,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def _get_existing_category_ids(session: AsyncSession) -> set[str]:
    """Retorna o conjunto de IDs de categorias já presentes no banco."""
    result = await session.execute(select(Category.id))
    return {row[0] for row in result.fetchall()}


async def _upsert_category(session: AsyncSession, data: dict) -> None:
    """Faz INSERT OR UPDATE de uma categoria usando ON CONFLICT DO UPDATE."""
    stmt = (
        pg_insert(Category)
        .values(
            id=data["id"],
            name=data["name"],
            parent_id=data.get("parent_id"),
            level=data.get("level", 0),
            total_items=data.get("total_items", 0),
            path_json=data.get("path_json", []),
            updated_at=datetime.now(timezone.utc),
        )
        .on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": data["name"],
                "parent_id": data.get("parent_id"),
                "level": data.get("level", 0),
                "total_items": data.get("total_items", 0),
                "path_json": data.get("path_json", []),
                "updated_at": datetime.now(timezone.utc),
            },
        )
    )
    await session.execute(stmt)


async def _record_changes(
    session: AsyncSession,
    job_id,
    added_ids: set[str],
    removed_ids: set[str],
    all_categories: dict[str, dict],
    pre_existing: dict[str, dict],
) -> None:
    """Registra adições e remoções no ChangeLog."""
    entries: list[ChangeLog] = []

    for cat_id in added_ids:
        cat = all_categories.get(cat_id, {})
        entries.append(
            ChangeLog(
                change_type="added",
                category_id=cat_id,
                category_name=cat.get("name", cat_id),
                parent_id=cat.get("parent_id"),
                import_job_id=job_id,
            )
        )

    for cat_id in removed_ids:
        cat = pre_existing.get(cat_id, {})
        entries.append(
            ChangeLog(
                change_type="removed",
                category_id=cat_id,
                category_name=cat.get("name", cat_id),
                parent_id=cat.get("parent_id"),
                import_job_id=job_id,
            )
        )

    if entries:
        session.add_all(entries)
        await session.flush()


async def _update_job(
    session: AsyncSession,
    job_id,
    status: str,
    processed: int,
    total_estimated: int,
    error_count: int,
) -> None:
    """Atualiza o ImportJob com o resultado final."""
    await session.execute(
        update(ImportJob)
        .where(ImportJob.id == job_id)
        .values(
            status=status,
            processed=processed,
            total_estimated=total_estimated,
            error_count=error_count,
            finished_at=datetime.now(timezone.utc),
        )
    )
    await session.commit()


# ---------------------------------------------------------------------------
# Lógica principal (async)
# ---------------------------------------------------------------------------


async def _run_import(task_self, triggered_by: str) -> dict:
    """Executa a importação completa de forma assíncrona."""
    redis_client = redis_sync.from_url(settings.REDIS_URL, decode_responses=True)
    job_id = None  # rastreado para poder marcar como failed em caso de exceção

    try:
        # 1. Verificar job em execução e criar ImportJob
        async with _WorkerSession() as session:
            running = await _get_running_job(session)
            if running:
                return {
                    "status": "error",
                    "message": f"Já existe um job em execução: {running.id}",
                    "job_id": str(running.id),
                }

            # 2. Criar ImportJob
            job = await _create_job(session, triggered_by)
            job_id = job.id
            channel = f"import:progress:{job_id}"

        logger.info("Iniciando importação — job_id=%s triggered_by=%s", job_id, triggered_by)

        # Captura IDs e dados existentes antes da importação (sessão separada)
        async with _WorkerSession() as session:
            pre_existing_ids = await _get_existing_category_ids(session)
            # Carrega dados básicos das categorias existentes para o ChangeLog de remoções
            result = await session.execute(
                select(Category.id, Category.name, Category.parent_id).where(
                    Category.id.in_(pre_existing_ids)
                )
            )
            pre_existing_data: dict[str, dict] = {
                row[0]: {"name": row[1], "parent_id": row[2]}
                for row in result.fetchall()
            }

        # 3. Buscar árvore completa via ML API
        client = MercadoLivreClient()
        root_categories = client.get_root_categories()
        total_roots = len(root_categories)

        all_fetched: dict[str, dict] = {}
        error_count = 0
        processed = 0

        # Estimativa inicial: cada raiz tem em média ~100 subcategorias
        total_estimated = total_roots * 100

        def _publish_progress(current_name: str) -> None:
            nonlocal processed
            processed += 1
            percent = round((processed / max(total_estimated, 1)) * 100, 1)
            event = {
                "processed": processed,
                "total_estimated": total_estimated,
                "percent": min(percent, 99.9),  # reserva 100% para o completed
                "current_category": current_name,
                "status": "running",
            }
            try:
                redis_client.publish(channel, json.dumps(event))
            except Exception as pub_exc:  # noqa: BLE001
                logger.warning("Falha ao publicar progresso no Redis: %s", pub_exc)

        for root in root_categories:
            root_id = root["id"]
            logger.info("Buscando árvore de %s (%s)", root["name"], root_id)

            # Adiciona a própria raiz ao conjunto
            all_fetched[root_id] = root

            try:
                subtree = client.fetch_full_tree(
                    root_id=root_id,
                    progress_callback=_publish_progress,
                    delay_ms=150,
                )
                for cat in subtree:
                    all_fetched[cat["id"]] = cat
            except Exception as fetch_exc:  # noqa: BLE001
                logger.error("Erro ao buscar árvore de %s: %s", root_id, fetch_exc)
                error_count += 1

        # Atualiza estimativa real após coleta
        total_estimated = len(all_fetched)

        # 4. Upsert de todas as categorias no banco
        async with _WorkerSession() as session:
            for cat_data in all_fetched.values():
                try:
                    await _upsert_category(session, cat_data)
                except Exception as upsert_exc:  # noqa: BLE001
                    logger.error("Erro ao fazer upsert de %s: %s", cat_data.get("id"), upsert_exc)
                    error_count += 1

            await session.commit()

        # 5. Detectar adições e remoções
        new_ids = set(all_fetched.keys())
        added_ids = new_ids - pre_existing_ids
        removed_ids = pre_existing_ids - new_ids

        logger.info(
            "Mudanças detectadas — adicionadas: %d, removidas: %d",
            len(added_ids),
            len(removed_ids),
        )

        # 6. Registrar mudanças no ChangeLog
        if added_ids or removed_ids:
            async with _WorkerSession() as session:
                await _record_changes(
                    session,
                    job_id=job_id,
                    added_ids=added_ids,
                    removed_ids=removed_ids,
                    all_categories=all_fetched,
                    pre_existing=pre_existing_data,
                )
                await session.commit()

        # 7. Atualizar ImportJob com status final
        # Marca como 'completed' mesmo com erros parciais; error_count indica falhas individuais
        final_status = "completed"
        async with _WorkerSession() as session:
            await _update_job(
                session,
                job_id=job_id,
                status=final_status,
                processed=len(all_fetched),
                total_estimated=total_estimated,
                error_count=error_count,
            )

        # 8. Publicar evento final e armazenar no Redis com TTL de 300s
        final_event = {
            "processed": len(all_fetched),
            "total_estimated": total_estimated,
            "percent": 100.0,
            "current_category": "",
            "status": "completed",
            "added": len(added_ids),
            "removed": len(removed_ids),
            "error_count": error_count,
        }
        try:
            redis_client.publish(channel, json.dumps(final_event))
            # Armazena o último evento com TTL de 300s para consulta posterior
            redis_client.setex(f"{channel}:last", 300, json.dumps(final_event))
        except Exception as redis_exc:  # noqa: BLE001
            logger.warning("Falha ao publicar evento final no Redis: %s", redis_exc)

        logger.info(
            "Importação concluída — job_id=%s categorias=%d erros=%d",
            job_id,
            len(all_fetched),
            error_count,
        )

        return {
            "status": final_status,
            "job_id": str(job_id),
            "processed": len(all_fetched),
            "added": len(added_ids),
            "removed": len(removed_ids),
            "error_count": error_count,
        }

    except Exception as exc:
        logger.exception("Erro não tratado em _run_import (job_id=%s): %s", job_id, exc)
        await _fail_job(job_id)
        raise

    finally:
        redis_client.close()


async def _fail_job(job_id) -> None:
    """Marca o job como 'failed' em caso de exceção não tratada."""
    if job_id is None:
        return
    try:
        async with _WorkerSession() as session:
            await session.execute(
                update(ImportJob)
                .where(ImportJob.id == job_id)
                .values(
                    status="failed",
                    finished_at=datetime.now(timezone.utc),
                )
            )
            await session.commit()
    except Exception as exc:  # noqa: BLE001
        logger.error("Falha ao marcar job %s como failed: %s", job_id, exc)


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------


@celery_app.task(bind=True, name="app.workers.import_task.import_categories")
def import_categories(self, triggered_by: str = "manual") -> dict:
    """
    Importa todas as categorias e subcategorias do MLB.

    1. Verifica se já existe job em execução (retorna erro se sim)
    2. Cria ImportJob com status 'running'
    3. Busca árvore completa via fetch_full_tree para cada Root_Category
    4. Faz upsert de cada categoria no PostgreSQL
    5. Detecta adições/remoções comparando com estado anterior
    6. Registra mudanças no ChangeLog
    7. Publica eventos de progresso no Redis (canal 'import:progress:{job_id}')
    8. Atualiza ImportJob com status 'completed' ou 'failed'

    Args:
        triggered_by: Origem do disparo — ``"manual"`` ou ``"scheduler"``.

    Returns:
        Dict com ``status``, ``job_id``, ``processed``, ``added``,
        ``removed`` e ``error_count``.
    """
    try:
        return asyncio.run(_run_import(self, triggered_by))
    except Exception as exc:
        logger.exception("Erro não tratado na tarefa import_categories: %s", exc)
        raise
