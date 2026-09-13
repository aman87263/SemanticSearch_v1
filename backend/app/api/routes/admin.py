from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.response_factory import success
from app.dependencies.auth import CurrentUser, require_admin
from app.schemas.common.api_response import ApiResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=ApiResponse[dict])
def admin_users(user: Annotated[CurrentUser, Depends(require_admin)]):
    return success(
        data={
            "mode": "admin",
            "user_id": user.user_id,
            "roles": user.roles,
        }
    )


@router.get("/audit", response_model=ApiResponse[dict])
def admin_audit(user: Annotated[CurrentUser, Depends(require_admin)]):
    return success(
        data={
            "audit_events": [
                {
                    "actor_user_id": user.user_id,
                    "action": "ADMIN_AUDIT_VIEW",
                    "target_type": "admin_audit",
                    "target_id": None,
                    "metadata": {"scope": "admin"},
                }
            ]
        }
    )
