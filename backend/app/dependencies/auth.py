from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from pydantic import BaseModel


class CurrentUser(BaseModel):
    user_id: str | None = None
    roles: list[str] = []
    authenticated: bool = False
    auth_header: str | None = None
    identity_provider: str | None = None


class AuthzError(BaseModel):
    code: str
    message: str


def get_current_user(
    request: Request,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> CurrentUser:
    """Read a demo/test auth context from headers and keep a Keycloak-friendly seam.

    Phase 1 scaffold:
    - Authorization header carries a bearer token
    - X-User-Id carries the user identity
    - X-User-Role carries the user's role
    - X-Identity-Provider can override the default provider label and maps cleanly
      to an OIDC provider such as Keycloak.

    This intentionally remains database-free and route-agnostic so the
    authentication migration can be layered later without changing the
    dependency shape.
    """

    user_id = request.headers.get("X-User-Id")
    raw_roles = request.headers.get("X-User-Role") or "USER"
    roles = [role.strip().upper() for role in raw_roles.split(",") if role.strip()]

    # Accept any bearer-shaped token in the initial scaffold.
    token = authorization if authorization else request.headers.get("Authorization")
    provider = request.headers.get("X-Identity-Provider") or "demo-header"

    # If the runtime is deliberately sending a Keycloak device route or a
    # configured provider label, use that instead of the demo default.
    if request.headers.get("X-Identity-Provider"):
        provider = request.headers.get("X-Identity-Provider")

    return CurrentUser(
        user_id=user_id,
        roles=roles,
        authenticated=bool(user_id and token),
        auth_header=token,
        identity_provider=provider,
    )


def require_authenticated_user(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    if not current_user.authenticated:
        raise HTTPException(status_code=401, detail="Authentication required")
    return current_user


def require_admin(
    current_user: Annotated[CurrentUser, Depends(require_authenticated_user)],
) -> CurrentUser:
    if "ADMIN" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
