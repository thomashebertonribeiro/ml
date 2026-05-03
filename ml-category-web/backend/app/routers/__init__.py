"""
Routers package — exports all APIRouter instances for registration in main.py.

Usage::

    from app.routers import auth, categories, changes, dashboard, export, import_router, public, scheduler
    app.include_router(auth.router)
    app.include_router(categories.router)
    ...
"""

from app.routers import (
    auth,
    categories,
    changes,
    dashboard,
    export,
    import_router,
    public,
    scheduler,
)

__all__ = [
    "auth",
    "categories",
    "changes",
    "dashboard",
    "export",
    "import_router",
    "public",
    "scheduler",
]
