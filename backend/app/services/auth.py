from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, status

from app.config import settings

ROLE_CAPABILITIES = {
    "admin": ["read", "operate", "review", "publish", "settings"],
    "editor": ["read", "operate", "review", "publish"],
    "operator": ["read", "operate"],
}


def _role_tokens() -> dict[str, str]:
    return {
        "admin": settings.auth_admin_token,
        "editor": settings.auth_editor_token,
        "operator": settings.auth_operator_token,
    }


def get_current_role(
    x_auth_role: str | None = Header(default=None),
    x_auth_token: str | None = Header(default=None),
) -> str:
    if not settings.auth_enabled:
        return "admin"

    role = (x_auth_role or "").strip().lower()
    token = (x_auth_token or "").strip()
    role_tokens = _role_tokens()

    if role not in role_tokens:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication role is required")
    if token != role_tokens[role]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
    return role


def require_role(*allowed_roles: str) -> Callable[[str], str]:
    allowed = set(allowed_roles)

    def dependency(current_role: str = Depends(get_current_role)) -> str:
        if current_role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role permissions")
        return current_role

    return dependency
