from app.dependencies.auth import CurrentUser


class AuthorizationService:
    """Central authorization policy wrapper.

    Keeps the authorization checks in one place, as required by the updated
    plan. This is intentionally decoupled from database storage and can later
    consult profiles, roles and permissions repositories.
    """

    def user_has_role(self, user: CurrentUser, role: str) -> bool:
        return role.upper() in [r.upper() for r in user.roles]

    def can_read_private_document(self, user: CurrentUser, owner_id: str | None) -> bool:
        if self.user_has_role(user, "ADMIN"):
            return True
        if owner_id is not None and user.user_id == owner_id:
            return True
        return False

    def can_manage_public_documents(self, user: CurrentUser) -> bool:
        return self.user_has_role(user, "ADMIN")
