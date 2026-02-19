"""
Services package for SkillFlow CRM
"""
from services.auth import (
    get_current_user,
    require_ho_role,
    require_admin_role,
    require_manager_or_above,
    require_permission,
    has_permission,
    get_role_level,
)
from services.audit import AuditAction, create_audit_log
from services.soft_delete import soft_delete_document, restore_document, check_duplicate
from services.utils import calculate_end_date, get_or_create_sdc, create_training_roadmap

__all__ = [
    "get_current_user",
    "require_ho_role",
    "require_admin_role",
    "require_manager_or_above",
    "require_permission",
    "has_permission",
    "get_role_level",
    "AuditAction",
    "create_audit_log",
    "soft_delete_document",
    "restore_document",
    "check_duplicate",
    "calculate_end_date",
    "get_or_create_sdc",
    "create_training_roadmap",
]
