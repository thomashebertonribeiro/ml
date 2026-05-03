"""
Categories router.

Endpoints (all require authentication):
    GET /categories                          — list root categories
    GET /categories/search?q=&page=&page_size= — search by name
    GET /categories/{category_id}            — category detail with children
    GET /categories/{category_id}/children   — direct children
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_redis
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryDetail, CategoryOut, SearchResponse
from app.services import cache_service, category_service
from app.services.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/categories", tags=["categories"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _category_to_out(cat: Category) -> CategoryOut:
    """Convert a Category ORM instance to a CategoryOut Pydantic schema.

    The ORM stores the breadcrumb path as ``path_json`` (a list of dicts),
    while the schema exposes it as ``path_from_root`` (a list of PathNode).
    ``model_validate`` with ``from_attributes=True`` cannot bridge this name
    difference automatically, so we build the dict explicitly.
    """
    return CategoryOut.model_validate(
        {
            "id": cat.id,
            "name": cat.name,
            "parent_id": cat.parent_id,
            "level": cat.level,
            "total_items": cat.total_items,
            "path_from_root": cat.path_json or [],
        }
    )


def _category_to_detail(cat: Category) -> CategoryDetail:
    """Convert a Category ORM instance (with loaded children) to CategoryDetail."""
    return CategoryDetail.model_validate(
        {
            "id": cat.id,
            "name": cat.name,
            "parent_id": cat.parent_id,
            "level": cat.level,
            "total_items": cat.total_items,
            "path_from_root": cat.path_json or [],
            "children": [_category_to_out(child) for child in (cat.children or [])],
        }
    )


# ---------------------------------------------------------------------------
# GET /categories
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=list[CategoryOut],
    summary="List root categories",
)
async def list_root_categories(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),  # type: ignore[type-arg]
    _current_user: User = Depends(get_current_user),
) -> list[CategoryOut]:
    """Return all root categories (parent_id IS NULL), ordered by name.

    Results are cached in Redis for 5 minutes under the key
    ``"categories:roots"``.
    """
    cache_key = "categories:roots"

    cached = await cache_service.get_cached(redis, cache_key)
    if cached is not None:
        return [CategoryOut.model_validate(item) for item in cached]

    categories = await category_service.get_root_categories(db)
    out = [_category_to_out(cat) for cat in categories]

    await cache_service.set_cached(
        redis,
        cache_key,
        [item.model_dump() for item in out],
        ttl_seconds=300,
    )

    return out


# ---------------------------------------------------------------------------
# GET /categories/search
# ---------------------------------------------------------------------------


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Search categories by name",
)
async def search_categories(
    q: str = Query(..., description="Search term (minimum 2 characters)"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),  # type: ignore[type-arg]
    _current_user: User = Depends(get_current_user),
) -> SearchResponse:
    """Search categories whose name contains *q* (case-insensitive).

    Raises:
        ValidationError (HTTP 422): if *q* is shorter than 2 characters.
    """
    if len(q.strip()) < 2:
        raise ValidationError("O termo de busca deve ter pelo menos 2 caracteres.")

    cache_key = f"categories:search:{q.lower()}:p{page}:ps{page_size}"

    cached = await cache_service.get_cached(redis, cache_key)
    if cached is not None:
        return SearchResponse.model_validate(cached)

    items, total = await category_service.search_categories(
        db, query=q, page=page, page_size=page_size
    )
    out_items = [_category_to_out(cat) for cat in items]

    response = SearchResponse(
        items=out_items,
        total=total,
        page=page,
        page_size=page_size,
    )

    await cache_service.set_cached(
        redis,
        cache_key,
        response.model_dump(),
        ttl_seconds=300,
    )

    return response


# ---------------------------------------------------------------------------
# GET /categories/{category_id}
# ---------------------------------------------------------------------------


@router.get(
    "/{category_id}",
    response_model=CategoryDetail,
    summary="Get category details with children",
)
async def get_category(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> CategoryDetail:
    """Return full details for a category, including its direct children.

    Raises:
        NotFoundError (HTTP 404): if the category does not exist.
    """
    category = await category_service.get_category_by_id(db, category_id)
    if category is None:
        raise NotFoundError(f"Categoria '{category_id}' não encontrada.")

    return _category_to_detail(category)


# ---------------------------------------------------------------------------
# GET /categories/{category_id}/children
# ---------------------------------------------------------------------------


@router.get(
    "/{category_id}/children",
    response_model=list[CategoryOut],
    summary="List direct children of a category",
)
async def get_category_children(
    category_id: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[CategoryOut]:
    """Return the direct children of *category_id*, ordered by name.

    Raises:
        NotFoundError (HTTP 404): if the parent category does not exist.
    """
    # Verify the parent exists before returning children
    parent = await category_service.get_category_by_id(db, category_id)
    if parent is None:
        raise NotFoundError(f"Categoria '{category_id}' não encontrada.")

    children = await category_service.get_children(db, parent_id=category_id)
    return [_category_to_out(child) for child in children]
