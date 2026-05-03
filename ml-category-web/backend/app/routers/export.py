"""
Export router.

Endpoints (all require authentication):
    GET /export?format=json|csv&root_id=  — download category data as a file
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services import export_service
from app.services.exceptions import ValidationError

router = APIRouter(prefix="/export", tags=["export"])

_VALID_FORMATS = {"json", "csv"}


@router.get(
    "/",
    summary="Export categories as JSON or CSV",
)
async def export_categories(
    format: str = Query(..., description="Export format: 'json' or 'csv'"),
    root_id: str | None = Query(None, description="Export only the subtree of this category"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Download all categories (or a subtree) as a JSON or CSV file.

    Query parameters:
        format: ``json`` or ``csv`` (required).
        root_id: Optional category ID. When provided, only the subtree
            rooted at that category is exported.

    Returns:
        A ``StreamingResponse`` with ``Content-Disposition: attachment``
        and the appropriate ``Content-Type``.

    Raises:
        ValidationError (HTTP 422): if *format* is not ``json`` or ``csv``.
        NotFoundError (HTTP 404): if the database has no categories, or if
            *root_id* does not exist.
    """
    fmt = format.lower().strip()
    if fmt not in _VALID_FORMATS:
        raise ValidationError(
            f"Formato inválido: '{format}'. Use 'json' ou 'csv'."
        )

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")

    if fmt == "json":
        content = await export_service.export_json(db, root_id=root_id)
        filename = f"ml_categories_{timestamp}.json"
        media_type = "application/json"
    else:
        content = await export_service.export_csv(db, root_id=root_id)
        filename = f"ml_categories_{timestamp}.csv"
        media_type = "text/csv"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }

    return StreamingResponse(
        iter([content]),
        media_type=media_type,
        headers=headers,
    )
