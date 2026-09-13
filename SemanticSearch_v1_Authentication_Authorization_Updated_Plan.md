# SemanticSearch_v1 — Authentication & Authorization Updated Plan

## 1. Objective

Add enterprise-style authentication and authorization while keeping the application independent of Supabase Auth and minimizing future migration effort from Supabase PostgreSQL/pgvector to Oracle Database.

Core principle:

> Authentication, authorization, and application data are separate concerns.

Target separation:

- **Authentication:** standards-based OIDC/OAuth identity provider
- **Authorization:** FastAPI RBAC + resource ownership/visibility
- **Application data:** PostgreSQL now, Oracle DB later
- **RAG security:** authorization-aware retrieval before context assembly

---

## 2. Functional Requirements

### Authentication

Support:

- Google
- Microsoft / Outlook
- GitHub
- Logout

### Normal authenticated user

A `USER` can:

- See their own private documents.
- Search their own private documents.
- Search public documents.
- Upload private documents.
- Chat using their own private + public documents.

A `USER` cannot:

- See another user's private documents.
- Search another user's private documents.
- Retrieve another user's chunks through RAG.
- Delete another user's documents.
- Delete public documents.
- Upload public documents.
- Promote users to admin.

### Admin

An `ADMIN` can:

- See all documents.
- Search all documents.
- Upload private documents.
- Upload public documents.
- Delete documents.
- Manage users.
- Promote another user to admin.
- Demote another admin, subject to last-admin protection.
- Chat/search using another user's document scope.
- Manage public documents.

### Public documents

Only admins can create them.

They are:

- Searchable by anonymous users.
- Searchable by authenticated users.
- Searchable by admins.
- Not deletable by normal users.
- Deletable by admins.

### Anonymous users

They can:

- Search public documents.
- Optionally chat against public documents.

They cannot:

- Access private documents.
- Upload.
- Delete.
- Access private metadata, chunks, citations, or conversations.

---

## 3. Recommended Architecture

Do **not** make Supabase Auth the long-term authentication dependency if Supabase is expected to be replaced.

Use an OIDC/OAuth-compatible identity provider.

A strong portable/self-hosted option is **Keycloak**.

```text
                     Google
                       |
                    Microsoft
                       |
                     GitHub
                       |
                       v
               +----------------+
               | OIDC Identity  |
               |    Provider    |
               +-------+--------+
                       |
                    JWT/OIDC
                       |
                       v
+-------------+  +-------------+
| React/Vite  |->| FastAPI     |
| Frontend    |  | Backend     |
+-------------+  +------+------+ 
                       |
                 Authorization
                       |
             +---------+---------+
             |                   |
             v                   v
       Application DB        RAG Pipeline
       PostgreSQL now        Retrieval
       Oracle later         Reranking
                             Context
                             LLM
```

### Why this matters

Current:

```text
OIDC IdP -> FastAPI -> Supabase PostgreSQL
```

Future:

```text
OIDC IdP -> FastAPI -> Oracle Database
```

The authentication system does not need to change when the database changes.

---

## 4. Authentication vs Authorization

### Authentication

Answers:

> Who is this user?

Handled by the OIDC identity provider.

### Authorization

Answers:

> What can this user do?

Handled by FastAPI and the application's RBAC/resource model.

Never use email addresses as authorization rules.

Avoid:

```python
if user.email == "admin@example.com":
    ...
```

Use roles and permissions instead.

---

## 5. Identity Model

Do not use email as the primary user identity.

Use the stable OIDC subject/identity identifier:

```text
identity_id
```

Application profile:

```text
profiles
-------------------------
id
identity_id
email
display_name
avatar_url
created_at
updated_at
```

Email is useful metadata, but should not be the primary relationship key because email addresses can change.

---

## 6. RBAC Model

Initial roles:

```text
USER
ADMIN
```

Future possibilities:

```text
SUPER_ADMIN
ADMIN
POWER_USER
USER
VIEWER
```

Recommended permissions:

```text
documents.read
documents.upload
documents.delete
documents.search

chat.execute
chat.other_user_scope

users.read
users.manage

roles.manage

public_documents.upload
public_documents.delete
```

Relationship:

```text
User
  |
  v
user_roles
  |
  v
Role
  |
  v
role_permissions
  |
  v
Permission
```

---

## 7. Database Tables

Application-level tables:

```text
profiles
roles
permissions
user_roles
role_permissions
documents
document_chunks
conversations
messages
audit_logs
```

The application should not permanently depend on Supabase's `auth.users`.

Keep the authentication identity represented by `profiles.identity_id`.

---

## 8. Document Ownership and Visibility

Extend the existing document model with:

```text
owner_id
visibility
```

Conceptual model:

```text
documents
-------------------------
id
owner_id
name
size
file_hash
storage_key
visibility
uploaded_at
status
progress
chunk_count
...
```

Visibility values:

```text
PRIVATE
PUBLIC
```

---

## 9. Access Rules

### Private document

```text
owner_id = User A
visibility = PRIVATE
```

Accessible by:

```text
User A
ADMIN
```

Not accessible by:

```text
User B
Anonymous
```

### Public document

```text
owner_id = Admin
visibility = PUBLIC
```

Accessible by:

```text
Anonymous
USER
ADMIN
```

Deletion:

```text
Anonymous -> NO
USER      -> NO
ADMIN     -> YES
```

---

## 10. Authorization-Aware RAG

This is the most important security change.

Do not do:

```text
Retrieve everything
    ->
Send everything to LLM
    ->
Filter answer
```

Instead:

```text
User / Anonymous identity
          |
          v
Authorization scope
          |
          v
Secure retrieval filter
          |
          v
Hybrid retrieval
          |
          v
Reranking
          |
          v
Context assembly
          |
          v
LLM
```

Rules:

### Anonymous

```text
visibility = PUBLIC
```

### USER

```text
owner_id = current_user.id
OR
visibility = PUBLIC
```

### ADMIN

```text
all documents
```

The filter should be applied as early as possible, ideally at the database/retrieval query layer.

Unauthorized chunks must never reach the LLM context.

---

## 11. Admin "Chat as User" Design

Do not implement actual account impersonation.

Instead use an explicit target-user scope.

Example:

```text
Admin
  |
  v
Select user: John
  |
  v
Start chat
  |
  v
RAG scope:
John's private documents
+
public documents
```

Record both:

```text
actor_user_id = Admin
target_user_id = John
```

This allows auditability and prevents ambiguous impersonation behavior.

---

## 12. Admin User Management

Admin UI:

```text
Users

User                  Role      Action
------------------------------------------------
john@example.com      USER      Make Admin
jane@example.com      ADMIN     Remove Admin
```

Backend must independently enforce:

```text
USER  -> DENY
ADMIN -> ALLOW
```

Hiding the button in React is not security.

### Last-admin protection

Always keep at least one admin.

Reject:

- demoting the last admin
- removing the last admin
- deleting the last admin

---

## 13. Public Document Upload

Admin UI:

```text
Upload Document

File: company-policy.pdf

Visibility:
  ( ) Private
  ( ) Public

[Upload]
```

For normal users:

```text
Visibility = PRIVATE
```

Do not trust a client-supplied `visibility=PUBLIC` field from a normal user. The backend must enforce the role.

---

## 14. API Authorization

Introduce reusable FastAPI dependencies:

```python
get_current_user()
require_authenticated_user()
require_admin()
require_permission("documents.upload")
require_permission("documents.delete")
```

Example:

```python
@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: UUID,
    user=Depends(require_permission("documents.delete"))
):
    ...
```

For normal users, permission checks must also be combined with ownership checks.

```text
USER
  |
  v
permission check
  |
  v
document.owner_id == current_user.id
  |
  v
operation
```

Admins can operate across ownership boundaries according to their permissions.

---

## 15. Frontend Structure

Recommended additions:

```text
frontend/src/
├── pages/
│   ├── LoginPage
│   ├── ChatPage
│   ├── DocumentsPage
│   ├── SearchPage
│   ├── SettingsPage
│   └── AdminPage
│
├── services/
│   ├── authService
│   ├── documentService
│   ├── searchService
│   └── chatService
│
├── providers/
│   ├── AuthProvider
│   ├── ChatProvider
│   └── DocumentProvider
│
└── components/
    ├── auth/
    ├── admin/
    ├── chat/
    ├── document/
    └── common/
```

Protected routes:

```text
/login                 PUBLIC

/chat                  AUTHENTICATED
/documents             AUTHENTICATED
/search                AUTHENTICATED
/settings              AUTHENTICATED

/admin                 ADMIN
/admin/users           ADMIN
/admin/documents       ADMIN
```

Anonymous public search can remain available separately or operate in anonymous mode.

---

## 16. Logout

Logout should:

1. End the application session.
2. Clear client-side auth state.
3. Handle token/session expiry according to the OIDC flow.
4. Redirect to `/login` or the public landing page.

FastAPI must reject expired/invalid access tokens.

---

## 17. Audit Logging

Add:

```text
audit_logs
-------------------------
id
actor_user_id
action
target_type
target_id
metadata
created_at
```

Useful events:

```text
USER_LOGIN
USER_LOGOUT

DOCUMENT_UPLOADED
DOCUMENT_DELETED
PUBLIC_DOCUMENT_CREATED
PUBLIC_DOCUMENT_DELETED

USER_PROMOTED_TO_ADMIN
USER_DEMOTED_FROM_ADMIN

ADMIN_VIEWED_USER_DOCUMENTS
ADMIN_CHAT_WITH_USER_SCOPE

PERMISSION_DENIED
```

This becomes especially useful when AI agents/MCP tools are introduced.

---

## 18. Future Agent/MCP Compatibility

The authorization architecture should later support:

```text
User
  |
  v
Agent
  |
  v
Tool
  |
  v
Authorization
  |
  v
Resource
```

For example:

```text
User A
  |
  v
Email Agent
  |
  v
search_email()
  |
  v
permission check
  |
  v
User A's mailbox
```

An agent should never receive broader access than its authorized user scope unless an explicit privileged operation exists.

The same actor/target/scope concept can be reused for MCP tools.

---

## 19. Supabase -> Oracle Migration

The authentication layer should remain unchanged.

### Current

```text
OIDC IdP
   |
   v
FastAPI
   |
   v
Supabase PostgreSQL/pgvector
```

### Future

```text
OIDC IdP
   |
   v
FastAPI
   |
   v
Oracle Database
```

Keep database-specific operations behind repository/service abstractions.

Existing pattern:

```text
API
 |
 v
Service
 |
 v
Repository Interface
 |
 v
PostgreSQL Repository
```

Future:

```text
API
 |
 v
Service
 |
 v
Repository Interface
 |
 v
Oracle Repository
```

Avoid putting PostgreSQL/Supabase-specific SQL directly into route handlers.

---

## 20. Important RLS Consideration

Supabase PostgreSQL supports Row Level Security.

It can be useful as defense in depth while Supabase is used.

However, do not make the application's entire authorization architecture depend on Supabase RLS.

Oracle will become the future database.

Therefore:

```text
FastAPI authorization
        +
database-level controls where available
```

is preferable to:

```text
Supabase-only authorization
```

---

## 21. Implementation Phases

### Phase 1 — Identity

Implement:

- OIDC identity provider
- Google login
- Microsoft login
- GitHub login
- Session handling
- Logout
- React AuthProvider
- Login page

Do not change the RAG retrieval model yet.

### Phase 2 — Backend Authentication

Implement:

```text
get_current_user()
require_authenticated_user()
```

Protect appropriate document/search/chat APIs.

### Phase 3 — Application User Model

Create:

```text
profiles
```

Map OIDC identities to application users.

### Phase 4 — RBAC

Create:

```text
roles
permissions
user_roles
role_permissions
```

Implement:

```text
USER
ADMIN
```

and reusable permission dependencies.

### Phase 5 — Document Ownership

Add:

```text
owner_id
visibility
```

Define a migration policy for existing production documents.

Recommended initial policy:

```text
Existing documents -> initial ADMIN
```

This prevents existing data from becoming inaccessible.

### Phase 6 — Secure Retrieval

Modify:

- document listing
- document lookup
- hybrid retrieval
- reranking input
- context assembly
- chat
- citations

to enforce:

```text
Anonymous -> PUBLIC
USER      -> OWN + PUBLIC
ADMIN     -> ALL
```

### Phase 7 — Admin

Build:

- admin dashboard
- user management
- document management
- role management

### Phase 8 — Admin User-Scope Chat

Implement:

```text
actor_user_id
target_user_id
```

and audit it.

### Phase 9 — Public Documents

Implement admin-only public upload and anonymous public search.

### Phase 10 — Hardening

Add:

- audit logs
- rate limiting
- permission-denied logging
- session expiration
- secure OAuth/OIDC state handling
- admin last-user protection
- security tests

---

## 22. Testing Strategy

### Authentication

- Google login
- Microsoft login
- GitHub login
- Logout
- Expired session
- Invalid token

### Document isolation

```text
Anonymous -> public document = ALLOW
Anonymous -> private document = DENY

User A -> User A document = ALLOW
User A -> User B document = DENY
User A -> public document = ALLOW

Admin -> all documents = ALLOW
```

### Mutation

```text
User -> own private delete = ALLOW
User -> another user's delete = DENY
User -> public delete = DENY
Admin -> public delete = ALLOW
```

### Admin

```text
User -> make admin = DENY
Admin -> promote user = ALLOW
Last-admin demotion = DENY
```

### RAG security

```text
User A query
 -> User B chunks must never enter retrieval context.

Anonymous query
 -> Private chunks must never enter retrieval context.

Admin target-user query
 -> Target user's private docs + public docs.
```

---

## 23. Deployment Strategy

Do not combine the authentication migration with the database migration.

Recommended sequence:

```text
Current Oracle production
        |
        v
Add authentication
        |
        v
Test authentication
        |
        v
Add authorization/RBAC
        |
        v
Test user isolation
        |
        v
Add public documents
        |
        v
Add admin functionality
        |
        v
Add audit logging/security hardening
        |
        v
Migrate database
        |
        v
Oracle DB production
```

Keep the current working RAG deployment available until the new security model is proven.

---

## 24. Final Target Architecture

```text
                    Google
                       |
                    Microsoft
                       |
                     GitHub
                       |
                       v
              +------------------+
              | OIDC Identity    |
              | Provider         |
              +--------+---------+
                       |
                    JWT/OIDC
                       |
                       v
+-------------+  +----------------+
| React       |->| FastAPI        |
| Frontend    |  | Backend        |
+-------------+  +-------+--------+
                        |
                  Authentication
                        |
                  Authorization
                        |
              +---------+----------+
              |                    |
              v                    v
       Application DB        RAG Pipeline
       Oracle DB             Authorization-aware
       Users                 Retrieval
       Roles                 Reranking
       Documents             Context
       Chunks                LLM
       Chat
       Audit Logs
```

---

## 25. Success Criteria

- [ ] Google login works.
- [ ] Microsoft/Outlook login works.
- [ ] GitHub login works.
- [ ] Logout works.
- [ ] Anonymous users can search only public documents.
- [ ] Users can see only their own private documents.
- [ ] Users can search only their own private documents + public documents.
- [ ] Users cannot retrieve another user's private chunks through RAG.
- [ ] Admins can access all documents.
- [ ] Admins can explicitly select another user's document scope for chat.
- [ ] Admin scope actions are auditable.
- [ ] Admins can promote users.
- [ ] Last-admin protection works.
- [ ] Only admins can upload public documents.
- [ ] Normal users cannot delete public documents.
- [ ] Backend enforces authorization independently of React.
- [ ] Authentication does not depend on Supabase Auth.
- [ ] Supabase PostgreSQL can later be replaced by Oracle DB without rewriting authentication.
- [ ] Repository/service abstractions isolate database-specific code.
- [ ] RAG retrieval enforces authorization before LLM context assembly.
- [ ] Security tests cover cross-user document leakage.

---

## 26. Immediate Next Step

Before coding, inspect the current SemanticSearch_v1 implementation and database schema.

Specifically review:

```text
backend/app/
├── models/
├── repositories/
├── services/
├── routers/
├── schemas/
└── config/

frontend/src/
├── pages/
├── components/
├── services/
└── providers/
```

Then design the exact changes for:

1. OIDC authentication.
2. Current-user dependency.
3. Profile model.
4. RBAC schema.
5. Document ownership/visibility migration.
6. Authorization-aware retrieval.
7. Admin APIs.
8. Public-search behavior.
9. Audit logging.

Only then implement the changes incrementally.
