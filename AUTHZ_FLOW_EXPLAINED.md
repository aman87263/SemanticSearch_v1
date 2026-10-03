# Authentication and Authorization Flow — Implemented Scaffold

This note explains the first staged, testable authorization/authentication scaffolding that was added to the repository for the plan described in the attached design document.

## Objective

The repository had no real current-user abstraction, no admin dependency, no authorization service boundary, and no document visibility metadata model. The goal of the first implementation step is to create a small, route-compatible structural foundation that can be replaced later by a real OIDC/JWT identity provider and database-backed user/profile/role repositories.

## What was added

### 1. Current-user dependency

File: `backend/app/dependencies/auth.py`

This file now contains a `CurrentUser` model and two dependency primitives:

- `get_current_user()`
- `require_authenticated_user()`
- `require_admin()`

The dependency reads a test-friendly header pattern from the request:

- `Authorization: Bearer ...`
- `X-User-Id: ...`
- `X-User-Role: USER|ADMIN`

This gives the backend a consistent object shape for future OIDC/JWT mapping while preserving a zero-database dependency for the current test stage.

### 2. Auth route

File: `backend/app/api/routes/auth.py`

This route adds an initial `/api/auth/me` endpoint that returns the request’s parsed current user shape using the repository’s standard `ApiResponse` envelope.

It is intentionally lightweight and acts as a placeholder for the real identity extraction route that will later read an OIDC JWT and map claims to `profiles`.

### 3. Admin route

File: `backend/app/api/routes/admin.py`

This route introduces the minimal admin contract:

- `/api/admin/users`
- `/api/admin/audit`

The `/api/admin/users` route is protected by `require_admin()` and returns a success envelope for an admin-only view.
The `/api/admin/audit` route demonstrates the event-model hook that can eventually become a real audit repository and log stream.

### 4. Router inclusion

File: `backend/app/api/routes/__init__.py`

The router registry now includes:

- health
- auth
- admin
- document
- search
- chat

That unlocks the newly added auth/admin endpoints without changing the app’s existing route setup style.

### 5. Profile and role schema species

Files:

- `backend/app/schemas/auth/profile.py`
- `backend/app/schemas/auth/role.py`

These files introduce the application-level shape that the plan describes:

- a `Profile` model for `identity_id`, `email`, `display_name`, and `avatar_url`
- a `RoleName` enum with `USER` and `ADMIN`
- a `Role` and `Permission` model to anchor the RBAC direction

### 6. Authorization service

File: `backend/app/services/auth/authorization_service.py`

This service acts as the first central policy point that can later grow into:

- role check
- permission check
- ownership check
- visibility filter

In the current scaffold, it only provides a simple flavor of policy logic:

- `user_has_role()`
- `can_read_private_document()`
- `can_manage_public_documents()`

### 7. Document visibility contract

File: `backend/app/schemas/document/entities/document.py`

The domain entity now includes:

- `owner_id: str | None = None`
- `visibility: DocumentVisibility = DocumentVisibility.PRIVATE`

The enum introduces:

- `PRIVATE`
- `PUBLIC`

This aligns the document model with the architecture plan’s ownership and visibility model.

### 8. Document response contract

Files:

- `backend/app/schemas/document/responses/document_response.py`
- `backend/app/mappers/document_mapper.py`

The mapped DTO now carries the ownership and visibility fields, so the response layer is ready for projected front-end and service enforcement that separates private and public document access.

## Code flow

The flow is intentionally simple and testable:

1. The request reaches the FastAPI app through the global router.
2. The `/api/auth/me` route or `/api/admin/users` route uses the dependency injection pattern from the repo.
3. `get_current_user()` reads the request headers and creates a `CurrentUser` model.
4. `require_admin()` validates the role list and rejects non-admin callers with HTTP 403.
5. The route handles the request and returns the repository-style success envelope via `success(data=...)`.

For the document model, the route/service interplay remains consistent:

1. A `Document` domain object is created with a `DocumentVisibility` enum state.
2. `DocumentMapper` serializes that document DTO into the response representation.
3. The document entity now carries the security metadata needed for the next authorization-aware retrieval step.

## Why this is a staged scaffold

This implementation does not yet wire up:

- real OIDC/JWT validation
- real database-backed profiles and roles
- real repository/service checks for owner identity or public/private visibility
- secure retrieval filtering before chunk context assembly
- audit persistence beyond the in-memory route event example

Instead, it creates a precise seam for each of those topics.

## What to do next

The next natural step is to replace the header-driven `CurrentUser` dependency with a real JWT/OIDC claim parser and then connect it to a `ProfileRepository` and `RoleRepository`. After that, the document repository and retrieval service can be updated to enforce:

- anonymous → public only
- user → own private + public
- admin → all documents

That gives the project a clean path from the current skeleton to the final policy design described in the plan.


Great question! You're right to question this - it's a **defense-in-depth** architecture with **dual validation**. Let me explain the flow:

## Authentication Flow

### 1. **Login (Callback) - `/api/auth/session`**
```
Frontend → POST /api/auth/session {code, code_verifier}
         ← Backend exchanges code with Keycloak
         ← Backend stores refresh_token in SESSION_STORE[keyed by session_id]
         ← Backend sets HttpOnly cookie: semanticsearch_session=session_id
         ← Backend returns {access_token, ...} to frontend
Frontend → Stores access_token IN MEMORY only (never in localStorage)
```

### 2. **Subsequent API Calls (e.g., upload document)**
```
Frontend → GET /api/documents
         → Headers: Authorization: Bearer <in_memory_access_token>
         → Cookie: semanticsearch_session=session_id (auto via credentials:include)

Backend Middleware Chain:
┌─────────────────────────────────────────────────────────────┐
│ SessionValidationMiddleware                                 │
│   ✓ Validates session cookie exists                         │
│   ✓ Looks up session_id in SESSION_STORE                    │
│   ✓ Checks session not revoked                              │
│   ✓ Attaches session to request.state                       │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ get_current_user (Dependency)                               │
│   ✓ Extracts Bearer token from Authorization header         │
│   ✓ Validates JWT signature via Keycloak JWKS               │
│   ✓ Checks exp, aud, iss                                    │
│   ✓ Extracts claims: sub, realm_access.roles                │
│   ✓ Returns CurrentUser object                              │
└─────────────────────────────────────────────────────────────┘
```

## Why Both?

| Layer | Purpose | Protection |
|-------|---------|------------|
| **Session Cookie + SESSION_STORE** | Server-side session management | • Revocation (logout, token theft)<br>• Server controls session lifetime<br>• HttpOnly - XSS can't steal it |
| **Bearer Token (JWT)** | Stateless identity propagation | • Carries user claims (roles, sub)<br>• Validated cryptographically<br>• Works across microservices |

## Key Point: The access token is SHORT-LIVED

- Access token: ~5 min (from Keycloak)
- Refresh token: Stored ONLY in server-side SESSION_STORE (never sent to frontend)
- Session cookie: HttpOnly, SameSite=Lax, 7 days

When access token expires → Frontend calls `/auth/refresh` with cookie → Backend uses stored refresh_token to get new access_token from Keycloak → Returns new access_token to frontend.

This is the **BFF (Backend for Frontend) pattern** - the backend acts as a token broker, keeping refresh tokens off the browser entirely.

**Correct - the backend does NOT store the access token.** Here's the flow:

## Token Storage

| Token | Stored Where | Lifetime |
|-------|--------------|----------|
| **Access Token** | **Frontend memory only** (never persisted) | ~5 min |
| **Refresh Token** | **Backend SESSION_STORE** (keyed by session_id) | 7 days (or Keycloak default) |
| **Session Cookie** | Browser (HttpOnly) | 7 days |

## Code Evidence

**Backend auth.py - Session creation (`/auth/session`):**
```python
# Line ~250-260: Stores REFRESH token in server-side store
session = {
    "user_id": user_id,
    "roles": roles,
    "provider": "keycloak",
    "refresh_token": tokens.get("refresh_token"),  # <-- ONLY refresh token stored
    "created_at": now.isoformat(),
    ...
}
SESSION_STORE[session_id] = session

# Line ~265: Returns access_token to frontend (NOT stored)
return success(data={
    "authenticated": True,
    "access_token": access_token,  # <-- Sent to frontend, not stored
    "expires_in": expires_in,
    ...
})
```

**Backend auth.py - Refresh (`/auth/refresh`):**
```python
# Line ~396: Gets refresh_token from SESSION_STORE
refresh_token = session.get("refresh_token")

# Line ~417-429: Uses it to get NEW access_token from Keycloak
token_request = {
    "grant_type": "refresh_token",
    "client_id": KEYCLOAK_CLIENT_ID,
    "refresh_token": refresh_token,  # <-- Uses stored refresh token
}
# ... calls Keycloak token endpoint ...

# Line ~475-481: Returns NEW access_token (not stored)
return success(data={
    "authenticated": True,
    "access_token": access_token,  # <-- New access token sent back
    "expires_in": expires_in,
})
```

## Why This Design?

1. **Access tokens are short-lived** (5 min) - no point storing them server-side
2. **Refresh tokens are sensitive** - kept server-side, never touch the browser
3. **Stateless validation** - each request validates JWT locally via JWKS (no DB lookup for access token)
4. **Revocation** - only the refresh token in SESSION_STORE can be revoked (logout)

The backend is a **token broker** - it exchanges refresh tokens for access tokens on demand, but never persists access tokens.


## Logout Flow - What Gets Invalidated

### Backend Logout Endpoint (`/api/auth/logout`):
```python
@router.post("/logout")
def logout_session(request: Request, response: Response):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    
    if session_id:
        session = SESSION_STORE.get(session_id)
        if session:
            session["revoked"] = True        # ① Marks session revoked
        
        SESSION_STORE.pop(session_id, None)  # ② Deletes refresh token from store
    
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")  # ③ Clears cookie
    
    return success(data={"logged_out": True})
```

---

### What Happens to Each Artifact:

| Artifact | Location | On Logout | Who Clears It |
|----------|----------|-----------|---------------|
| **Session Cookie** | Browser (HttpOnly) | **Deleted** | Backend via `Set-Cookie: expires=Thu, 01 Jan 1970...` |
| **Refresh Token** | Backend `SESSION_STORE` | **Deleted** (`SESSION_STORE.pop`) | Backend |
| **Access Token** | Frontend memory | **Cleared** | Frontend (`setAccessToken(null)`) |

---

### What Breaks the API (causes 401 → redirect to login)

**The middleware chain checks in order:**

```python
# 1. SessionValidationMiddleware (runs FIRST)
session = get_session_from_cookie(request)
if not session:
    return 401 {SESSION_INVALID}  # ← NO COOKIE = BREAKS HERE

# 2. get_current_user dependency (runs SECOND)  
token = extract_bearer_token(authorization)
claims = _decode_claims_from_keycloak(token)
if not claims:
    return 401 {Invalid authentication token}  # ← EXPIRED/INVALID JWT = BREAKS HERE
```

---

### Timeline After Logout:

| Time | Request | Cookie | Access Token | Result |
|------|---------|--------|--------------|--------|
| T+0 | Logout clicked | ✓ Sent | ✓ Sent | 200 OK (cookie deleted, store cleared) |
| T+1 | Any API call | ✗ **Gone** | ✓ Still in memory | **401 SESSION_INVALID** (middleware #1) |
| T+5min | Any API call | ✗ Gone | ✗ Expired | 401 Invalid token (middleware #2) |

---

### The Redirect Trigger

**Frontend Sidebar logout handler:**
```typescript
const handleLogout = async () => {
    await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
    
    clearAuthSession();           // ← Clears in-memory access token
    notifyAuthChanged();          // ← Triggers re-render → shows "Login"
    
    window.location.assign(getKeycloakLogoutUrl(null));  // ← Full redirect
};
```

**The `notifyAuthChanged()` fires `auth-changed` event → `AuthProvider` re-evaluates `hasAuthToken()` → returns `false` → `ProtectedRoute` redirects to `/login`.**

---

### Key Insight

**The session cookie deletion is what immediately breaks subsequent API calls** - even if the access token is still valid in memory, the middleware rejects the request because the session cookie is gone.

This is by design: **logout = server-side session termination**, not just client-side token clearing.



                    React Router
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          /login       /chat      /documents
                         │
                         ▼
                 React Components
                         │
                         ▼
                Context Providers
              ┌────────┼─────────┐
              ▼        ▼         ▼
          AuthContext ChatContext DocumentContext
              │        │         │
              └────────┼─────────┘
                       ▼
                    Services
              ┌────────┼─────────┐
              ▼        ▼         ▼
          authService chatService documentService
              │        │         │
              └────────┼─────────┘
                       ▼
                    api.ts
                       │
                       ▼
                  httpClient.ts
                       │
                       ▼
                  HTTP / Backend