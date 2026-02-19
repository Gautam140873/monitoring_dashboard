"""
Routers package for SkillFlow CRM
"""
from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.master_data import router as master_data_router
from routers.resources import router as resources_router
from routers.sdcs import router as sdcs_router
from routers.dashboard import router as dashboard_router
from routers.ledger import router as ledger_router

__all__ = [
    "auth_router",
    "users_router",
    "master_data_router",
    "resources_router",
    "sdcs_router",
    "dashboard_router",
]
