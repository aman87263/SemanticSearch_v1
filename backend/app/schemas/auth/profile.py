from pydantic import BaseModel


class Profile(BaseModel):
    """Application-level identity profile.

    This intentionally separates provider identity from the local application
    account model, matching the plan's design requirement that authentication
    and application authorization remain distinct concerns.
    """

    id: str | None = None
    identity_id: str | None = None
    email: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
