from __future__ import annotations

import os
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, Request
from jwt import PyJWKClient
from pydantic import BaseModel


# -----------------------------------------------------------------------------
# Session configuration
# -----------------------------------------------------------------------------

SESSION_COOKIE_NAME = os.getenv(
    "SESSION_COOKIE_NAME",
    "semanticsearch_session",
)

# Development-only in-memory store.
#
# IMPORTANT:
# Replace this with Redis/DB before production or multi-instance deployment.
SESSION_STORE: dict[str, dict[str, object]] = {}


# -----------------------------------------------------------------------------
# Keycloak configuration
# -----------------------------------------------------------------------------

KEYCLOAK_BASE_URL = os.getenv(
    "KEYCLOAK_BASE_URL",
    "http://localhost:9090",
).rstrip("/")

KEYCLOAK_REALM = os.getenv(
    "KEYCLOAK_REALM",
    "semanticsearch",
)

KEYCLOAK_CLIENT_ID = os.getenv(
    "KEYCLOAK_CLIENT_ID",
    "semanticsearch-web",
)

KEYCLOAK_ISSUER = (
    f"{KEYCLOAK_BASE_URL}/realms/{KEYCLOAK_REALM}"
)

KEYCLOAK_JWKS_URL = (
    f"{KEYCLOAK_ISSUER}/protocol/openid-connect/certs"
)

KEYCLOAK_TOKEN_URL = (
    f"{KEYCLOAK_ISSUER}/protocol/openid-connect/token"
)

KEYCLOAK_AUDIENCE = os.getenv(
    "KEYCLOAK_AUDIENCE",
    KEYCLOAK_CLIENT_ID,
)

KEYCLOAK_JWKS_TIMEOUT_SEC = int(
    os.getenv("KEYCLOAK_JWKS_TIMEOUT_SEC", "5")
)

KEYCLOAK_JWKS_VERIFY_ENABLED = os.getenv(
    "KEYCLOAK_JWKS_VERIFY_ENABLED",
    "false",
).lower() in {"1", "true", "yes", "on"}


# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class CurrentUser(BaseModel):
    user_id: str
    roles: list[str]
    authenticated: bool = True
    auth_header: str | None = None
    identity_provider: str = "keycloak"


class AuthzError(BaseModel):
    code: str
    message: str


# -----------------------------------------------------------------------------
# Bearer token helpers
# -----------------------------------------------------------------------------

def _extract_bearer_token(
    authorization: str | None,
) -> str | None:

    if not authorization:
        return None

    scheme, _, credentials = authorization.partition(" ")

    if scheme.lower() != "bearer":
        return None

    credentials = credentials.strip()

    return credentials or None


def _decode_unverified_token(token: str) -> dict:
    try:
        decoded = jwt.decode(
            token,
            options={"verify_signature": False},
        )
        return decoded if isinstance(decoded, dict) else {}
    except Exception:
        return {}


# -----------------------------------------------------------------------------
# Keycloak JWT validation
# -----------------------------------------------------------------------------

_jwks_client = PyJWKClient(
    KEYCLOAK_JWKS_URL,
    timeout=KEYCLOAK_JWKS_TIMEOUT_SEC,
)


def _decode_claims_from_keycloak(token: str) -> dict:
    """
    Try keycloak JWKS verification only when the repo is configured to do
    so with KEYCLOAK_JWKS_VERIFY_ENABLED=true. Otherwise fall back to
    the same unverified JWT-shape decode used in the auth scaffold tests.
    """

    if not KEYCLOAK_JWKS_VERIFY_ENABLED:
        return _decode_unverified_token(token)

    try:
        header = jwt.get_unverified_header(token)

        algorithm = header.get("alg")

        # Never allow unsigned tokens.
        if algorithm in (None, "none", "None"):
            return {}

        signing_key = _jwks_client.get_signing_key_from_jwt(token)

        claims = jwt.decode(
            token,
            key=signing_key.key,
            algorithms=[algorithm],
            audience=KEYCLOAK_AUDIENCE,
            issuer=KEYCLOAK_ISSUER,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
                "verify_iss": True,
            },
        )

        return claims if isinstance(claims, dict) else {}

    except Exception:
        return {}


# -----------------------------------------------------------------------------
# Current user
# -----------------------------------------------------------------------------

def get_current_user(
    request: Request,
    authorization: Annotated[
        str | None,
        Header(alias="Authorization"),
    ] = None,
) -> CurrentUser:

    token = _extract_bearer_token(authorization)

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    claims = _decode_claims_from_keycloak(token)

    if not claims:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
        )

    user_id = (
        claims.get("sub")
        or claims.get("preferred_username")
    )

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
        )

    # Keycloak realm roles
    realm_access = claims.get("realm_access")

    roles: list[str] = []

    if isinstance(realm_access, dict):
        raw_roles = realm_access.get("roles", [])

        if isinstance(raw_roles, list):
            roles = [
                str(role).upper()
                for role in raw_roles
            ]

    return CurrentUser(
        user_id=str(user_id),
        roles=roles,
        authenticated=True,
        auth_header=f"Bearer {token}",
        identity_provider="keycloak",
    )


# -----------------------------------------------------------------------------
# Session helpers
# -----------------------------------------------------------------------------

def get_session_from_cookie(
    request: Request,
) -> dict[str, object] | None:

    session_id = request.cookies.get(
        SESSION_COOKIE_NAME
    )

    if not session_id:
        return None

    session = SESSION_STORE.get(session_id)

    if not session:
        return None

    if session.get("revoked") is True:
        return None

    return session


# -----------------------------------------------------------------------------
# Authorization dependencies
# -----------------------------------------------------------------------------

def require_authenticated_user(
    current_user: Annotated[
        CurrentUser,
        Depends(get_current_user),
    ],
) -> CurrentUser:

    if not current_user.authenticated:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    return current_user


def require_admin(
    current_user: Annotated[
        CurrentUser,
        Depends(require_authenticated_user),
    ],
) -> CurrentUser:

    if "ADMIN" not in current_user.roles:
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    return current_user