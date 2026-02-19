"""
Routers package for SkillFlow CRM
"""
from .auth import router as auth_router
from .users import router as users_router
from .master_data import router as master_data_router
from .resources import router as resources_router
from .sdcs import router as sdcs_router
from .dashboard import router as dashboard_router

__all__ = [
    "auth_router",
    "users_router",
    "master_data_router",
    "resources_router",
    "sdcs_router",
    "dashboard_router",
]
