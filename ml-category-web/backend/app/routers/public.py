"""
Public categories router — no authentication required.

All endpoints enforce a rate limit of 60 requests per minute per IP.

Endpoints:
    GET /public/categories                          — root categories (cache 5 min)
    GET /public/categories/search?q=&page=&page_size= — search by name
    GET /public/categories/{category_id}            — category detail with children
    GET /public/categories/{category_id}/children   — direct children
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, Response
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_redis
from app.models.category import Category
from app.schemas.category import CategoryDetail, CategoryOut, SearchResponse
from app.services import cache_service, category_service
from app.services.exceptions import NotFoundError, RateLimitError, ValidationError
from app.services.rate_limiter import check_rate_limit

router = APIRouter(prefix="/public", tags=["public"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _category_to_out(cat: Category) -> CategoryOut:
    """Convert a Category ORM instance to CategoryOut."""
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


async def _enforce_rate_limit(request: Request, redis: Redis) -> None:  # type: ignore[type-arg]
    """Check the rate limit for the requesting IP.

    Raises:
        RateLimitError (HTTP 429): if the IP has exceeded 60 req/min.
    """
    client_ip: str = request.client.host if request.client else "unknown"
    allowed, retry_after = await check_rate_limit(redis, client_ip)
    if not allowed:
        raise RateLimitError(
            f"Limite de requisições excedido. Tente novamente em {retry_after} segundos.",
            retry_after=retry_after,
        )


# ---------------------------------------------------------------------------
# GET /public/categories
# ---------------------------------------------------------------------------


@router.get(
    "/categories",
    response_model=list[CategoryOut],
    summary="List root categories (public)",
)
async def list_root_categories(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),  # type: ignore[type-arg]
) -> list[CategoryOut]:
    """Return all root categories (parent_id IS NULL), ordered by name.

    Results are cached in Redis for 5 minutes under the key
    ``"public:categories:roots"``.

    Raises:
        RateLimitError (HTTP 429): if the IP has exceeded 60 req/min.
    """
    await _enforce_rate_limit(request, redis)

    cache_key = "public:categories:roots"

    cached = await cache_service.get_cached(redis, cache_key)
    if cached is not None:
        items = [CategoryOut.model_validate(item) for item in cached]
        response.headers["X-Total-Count"] = str(len(items))
        return items

    categories = await category_service.get_root_categories(db)
    out = [_category_to_out(cat) for cat in categories]

    await cache_service.set_cached(
        redis,
        cache_key,
        [item.model_dump() for item in out],
        ttl_seconds=300,
    )

    response.headers["X-Total-Count"] = str(len(out))
    return out


# ---------------------------------------------------------------------------
# GET /public/categories/search
# ---------------------------------------------------------------------------


@router.get(
    "/categories/search",
    response_model=SearchResponse,
    summary="Search categories by name (public)",
)
async def search_categories(
    request: Request,
    response: Response,
    q: str = Query(..., description="Search term (minimum 2 characters)"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),  # type: ignore[type-arg]
) -> SearchResponse:
    """Search categories whose name contains *q* (case-insensitive).

    Raises:
        RateLimitError (HTTP 429): if the IP has exceeded 60 req/min.
        ValidationError (HTTP 422): if *q* is shorter than 2 characters.
    """
    await _enforce_rate_limit(request, redis)

    if len(q.strip()) < 2:
        raise ValidationError("O termo de busca deve ter pelo menos 2 caracteres.")

    items, total = await category_service.search_categories(
        db, query=q, page=page, page_size=page_size
    )
    out_items = [_category_to_out(cat) for cat in items]

    search_response = SearchResponse(
        items=out_items,
        total=total,
        page=page,
        page_size=page_size,
    )

    response.headers["X-Total-Count"] = str(total)
    return search_response


# ---------------------------------------------------------------------------
# GET /public/categories/{category_id}
# ---------------------------------------------------------------------------


@router.get(
    "/categories/{category_id}",
    response_model=CategoryDetail,
    summary="Get category details with children (public)",
)
async def get_category(
    category_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),  # type: ignore[type-arg]
) -> CategoryDetail:
    """Return full details for a category, including its direct children.

    Raises:
        RateLimitError (HTTP 429): if the IP has exceeded 60 req/min.
        NotFoundError (HTTP 404): if the category does not exist.
    """
    await _enforce_rate_limit(request, redis)

    category = await category_service.get_category_by_id(db, category_id)
    if category is None:
        raise NotFoundError(f"Categoria '{category_id}' não encontrada.")

    return _category_to_detail(category)


# ---------------------------------------------------------------------------
# GET /public/categories/{category_id}/children
# ---------------------------------------------------------------------------


@router.get(
    "/categories/{category_id}/children",
    response_model=list[CategoryOut],
    summary="List direct children of a category (public)",
)
async def get_category_children(
    category_id: str,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),  # type: ignore[type-arg]
) -> list[CategoryOut]:
    """Return the direct children of *category_id*, ordered by name.

    Raises:
        RateLimitError (HTTP 429): if the IP has exceeded 60 req/min.
        NotFoundError (HTTP 404): if the parent category does not exist.
    """
    await _enforce_rate_limit(request, redis)

    parent = await category_service.get_category_by_id(db, category_id)
    if parent is None:
        raise NotFoundError(f"Categoria '{category_id}' não encontrada.")

    children = await category_service.get_children(db, parent_id=category_id)
    out = [_category_to_out(child) for child in children]

    response.headers["X-Total-Count"] = str(len(out))
    return out
