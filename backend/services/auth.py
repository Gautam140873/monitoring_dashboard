"""
Authentication and authorization services for SkillFlow CRM
"""
from fastapi import HTTPException, Depends, Request
from datetime import datetime, timezone

from ..database import db
from ..models.user import User
from ..config import ROLES


def has_permission(user_role: str, required_permission: str) -> bool:
    """Check if a role has a specific permission"""
    role_config = ROLES.get(user_role, ROLES["sdc"])
    permissions = role_config["permissions"]
    
    # Admin has all permissions
    if "*" in permissions:
        return True
    
    # Check exact match
    if required_permission in permissions:
        return True
    
    # Check wildcard (e.g., "sdcs:*" matches "sdcs:read")
    permission_parts = required_permission.split(":")
    for perm in permissions:
        perm_parts = perm.split(":")
        if len(perm_parts) >= 1 and perm_parts[0] == permission_parts[0]:
            if len(perm_parts) >= 2 and perm_parts[1] == "*":
                return True
    
    return False


def get_role_level(role: str) -> int:
    """Get the hierarchy level of a role"""
    return ROLES.get(role, ROLES["sdc"])["level"]


async def get_current_user(request: Request) -> User:
    """Get current authenticated user from session token"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_doc = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    user_doc = await db.users.find_one({"user_id": session_doc["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_doc)


async def require_ho_role(user: User = Depends(get_current_user)) -> User:
    """Require HO (Head Office) or Admin role"""
    if user.role not in ["ho", "admin"]:
        raise HTTPException(status_code=403, detail="HO or Admin access required")
    return user


async def require_admin_role(user: User = Depends(get_current_user)) -> User:
    """Require Admin role only"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def require_manager_or_above(user: User = Depends(get_current_user)) -> User:
    """Require Manager, HO, or Admin role"""
    if user.role not in ["manager", "ho", "admin"]:
        raise HTTPException(status_code=403, detail="Manager or higher access required")
    return user


def require_permission(permission: str):
    """Decorator factory to require specific permission"""
    async def permission_checker(user: User = Depends(get_current_user)) -> User:
        if not has_permission(user.role, permission):
            raise HTTPException(
                status_code=403, 
                detail=f"Permission denied: {permission} required"
            )
        return user
    return permission_checker
