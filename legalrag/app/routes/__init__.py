from .documents import router as documents_router
from .search import router as search_router
from .generation import router as generation_router
from .settings import router as settings_router
from .cases import router as cases_router

__all__ = [
    "documents_router",
    "search_router",
    "generation_router",
    "settings_router",
    "cases_router",
]
