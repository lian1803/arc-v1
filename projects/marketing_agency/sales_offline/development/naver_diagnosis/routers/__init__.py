"""
Routers 패키지
"""
from routers.search import router as search_router
from routers.crawl import router as crawl_router
from routers.ppt import router as ppt_router
from routers.manual import router as manual_router
from routers.history import router as history_router
from routers.message import router as message_router
from routers.batch import router as batch_router
from routers.crm import router as crm_router

__all__ = [
    "search_router",
    "crawl_router",
    "ppt_router",
    "manual_router",
    "history_router",
    "message_router",
    "batch_router",
    "crm_router",
]
