# AuthZ Next Implementation Tiers

This note converts the current repository state into a sequenced implementation plan that makes the authorization scaffold genuinely enforceable in the next step.

## Current verified state

The implemented scaffold sets up the structural defense points described in the plan:

- a header-driven `CurrentUser` model and dependency pattern in `backend/app/dependencies/auth.py`
- a role-aware `require_admin()` dependency
- an auth route under `/api/auth/me`
- an admin route under `/api/admin/users` and `/api/admin/audit`
- profile and role schema stubs for the application identity model
- a document schema with `owner_id` and `visibility`
- a response mapper carrying those new fields forward into the document DTO

The existing regression tests confirm that this scaffold compiles through the repository’s standard response envelope and route registration shape.

## Important gap

The plan’s structural model has been added, but the actual enforcement model is not yet linked to the real data flow:

- document upload routes do not accept or enforce a `current_user`
- document list and delete endpoints remain unguarded
- search and chat routes are not parameterized by authorization scope
- retrieval receives no `CurrentUser` or visibility policy input
- `require_permission()` abstraction is not yet present
- the upload document service still assigns the placeholder `owner_id = "system"`

That means the repository has the policy vocabulary and the model fields, but it has not yet connected them to the retrieval, document, and chat flows.

## Recommended next tiers

### Tier 1 — Protect the route boundary

Implement the route-wrapper dependencies in the real API:

1. Add `require_authenticated_user()` to all document routes, search routes, and chat routes that are meant to be personal or private.
2. Add `require_admin()` to the admin endpoints already scaffolded.
3. Use `CurrentUser` to carry `roles`, `user_id`, and provider metadata through the route chain.

This is the first enforcement step.

### Tier 2 — Introduce the permission dependency

Create a reusable dependency pattern exactly as described by the plan:

```python
require_permission("documents.delete")
require_permission("documents.upload")
```

This should be built atop `AuthorizationService` so the route guard is not just a simple role string check.

### Tier 3 — Route and service ownership enforcement

The document service should no longer assign `owner_id = "system"`. Instead:

- `owner_id` should come from the authenticated `CurrentUser.user_id`
- `visibility` should default to `PRIVATE` for normal users
- `visibility=PUBLIC` should be accepted only for an admin or authorized public-upload policy path

That creates a clean upload ownership and visibility source of truth.

### Tier 4 — Scope-aware retrieval filtering

The crucial phase is authorization-aware retrieval:

- `Anonymous -> PUBLIC`
- `USER -> OWN + PUBLIC`
- `ADMIN -> ALL`

This requires the retrieval pipeline to carry `CurrentUser` through the call chain:

```python
RetrievalService.retrieve(query, limit, document_id, current_user)
```

The retrieval query path must then filter chunks by a visibility and ownership policy before context assembly and before the LLM receives a message.

### Tier 5 — Public search and anonymous mode

The plan describes an anonymous public search mode. This should be implemented with a separate policy branch:

- anonymous identity: only `PUBLIC` visibility documents may be searched or retrieved
- normal user identity: `PRIVATE` ownership documents that belong to the current user plus public documents
- admin identity: all documents

This branch should be a single switch in the retrieval service so the policy does not drift across routes.

### Tier 6 — Auditability

The `/api/admin/audit` scaffold should be backed by a real audit log service that records:

- actor identity
- action
- target type
- target id
- metadata

This event stream should be consistent with the architecture plan’s event list and should be inserted in the same central place where authorization decisions are made.

## Implementation sequence

1. Wire `require_authenticated_user()` through `/documents`, `/search`, and `/chat` route entry points.
2. Make the current document and search services receive a real `CurrentUser` object.
3. Add `require_permission()` on the permission-sensitive route declarations.
4. Change upload flow so `owner_id` is the actual authenticated user and visibility is set from policy rather than client trust.
5. Modify the retrieval path so only allowed document chunks reach the context builder and question-answering flow.
6. Extend the admin audit endpoint into a proper audit service and event repository abstraction.

## Design principle

The repository should maintain one direction of policy truth:

- Authentication is a provider concern.
- Authorization is a FastAPI + service policy concern.
- Application data remains a repository concern.

That separation is the key migration freedom promised by the plan.
