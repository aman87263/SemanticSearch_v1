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
