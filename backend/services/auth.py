"""
Authentication and authorization services for SkillFlow CRM
"""
from fastapi import HTTPException, Depends, Request
from datetime import datetime, timezone

from database import db
from models.user import User
from config import ROLES


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


async def check_sdc_access(user: User, sdc_id: str, action: str = "read") -> bool:
    """
    Check if user has access to a specific SDC.
    
    Refined RBAC Rules:
    - Admin/HO: Full access to all SDCs
    - Manager: Can only edit their assigned SDC, read-only for others
    - SDC: Can only access their assigned SDC
    """
    # Admin and HO have full access
    if user.role in ["admin", "ho"]:
        return True
    
    # Manager role - can edit only their assigned SDC
    if user.role == "manager":
        if action == "read":
            return True  # Managers can read all SDCs
        elif action in ["update", "delete"]:
            # Check if this manager is assigned to this SDC
            sdc = await db.sdcs.find_one({"sdc_id": sdc_id}, {"_id": 0})
            if sdc:
                # Check if user email matches manager_email or if user is assigned
                if user.assigned_sdc_id == sdc_id:
                    return True
                if sdc.get("manager_email") == user.email:
                    return True
            return False
    
    # SDC role - can only access their assigned SDC
    if user.role == "sdc":
        return user.assigned_sdc_id == sdc_id
    
    return False


async def require_sdc_access(sdc_id: str, action: str = "read"):
    """Dependency factory for SDC access control"""
    async def checker(user: User = Depends(get_current_user)) -> User:
        has_access = await check_sdc_access(user, sdc_id, action)
        if not has_access:
            if action == "read":
                raise HTTPException(status_code=403, detail="You don't have access to this SDC")
            else:
                raise HTTPException(
                    status_code=403, 
                    detail=f"You don't have permission to {action} this SDC. Only assigned managers can modify."
                )
        return user
    return checker
