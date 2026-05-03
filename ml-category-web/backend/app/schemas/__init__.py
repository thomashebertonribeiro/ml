"""
Pydantic schemas package.

Re-exports all request/response models so routers can import from
`app.schemas` directly, e.g.:

    from app.schemas import LoginRequest, TokenResponse, CategoryOut
"""

from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.category import (
    CategoryDetail,
    CategoryOut,
    PathNode,
    SearchResponse,
)
from app.schemas.change_log import (
    ChangeLogOut,
    ChangeSummaryItem,
)
from app.schemas.dashboard import DashboardStats
from app.schemas.import_job import (
    ImportStartResponse,
    ImportStatusOut,
    SSEProgressEvent,
)
from app.schemas.scheduler import (
    SchedulerConfigUpdate,
    SchedulerStatus,
)

__all__ = [
    # auth
    "LoginRequest",
    "RefreshRequest",
    "RegisterRequest",
    "TokenResponse",
    # category
    "CategoryDetail",
    "CategoryOut",
    "PathNode",
    "SearchResponse",
    # change_log
    "ChangeLogOut",
    "ChangeSummaryItem",
    # dashboard
    "DashboardStats",
    # import_job
    "ImportStartResponse",
    "ImportStatusOut",
    "SSEProgressEvent",
    # scheduler
    "SchedulerConfigUpdate",
    "SchedulerStatus",
]
