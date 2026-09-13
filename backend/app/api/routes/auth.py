from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.response_factory import success
from app.dependencies.auth import CurrentUser, get_current_user
from app.schemas.common.api_response import ApiResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/me", response_model=ApiResponse[dict])
def me(user: Annotated[CurrentUser, Depends(get_current_user)]):
    return success(
        data={
            "user_id": user.user_id,
            "roles": user.roles,
            "authenticated": user.authenticated,
            "provider": user.identity_provider,
        }
    )


@router.get("/keycloak/config", response_model=ApiResponse[dict])
def keycloak_config():
    return success(
        data={
            "provider": "keycloak",
            "realm": "master",
            "issuer": "http://localhost:9090/realms/master",
            "authorization_endpoint": "http://localhost:9090/realms/master/protocol/openid-connect/auth",
            "token_endpoint": "http://localhost:9090/realms/master/protocol/openid-connect/token",
            "userinfo_endpoint": "http://localhost:9090/realms/master/protocol/openid-connect/userinfo",
            "jwks_uri": "http://localhost:9090/realms/master/protocol/openid-connect/certs",
        }
    )
