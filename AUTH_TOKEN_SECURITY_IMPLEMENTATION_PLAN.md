# Auth Token Security Implementation Plan

This document converts the agreed security direction into an implementation checklist and links every step to the code that currently exists in the repository and the code that should be introduced.

## 1. Stop storing tokens in browser storage

Current code:
- Frontend session helper: `frontend/src/auth/session.ts`
- It writes `accessToken`, `refreshToken`, and `idToken` to `localStorage` in `persistAuthSession()`.
- This directly matches the current insecure storage pattern.

Target state:
- Remove all token material from `localStorage` and `sessionStorage`.
- Keep only an opaque browser session cookie (`HttpOnly`, `Secure`, `SameSite`) and an in-memory access token in the frontend view model.

Repository touchpoints:
- `persistAuthSession()` in `frontend/src/auth/session.ts`
- `clearAuthSession()` in `frontend/src/auth/session.ts`
- `LoginCallbackPage.tsx` in `frontend/src/pages/Login/LoginCallbackPage.tsx`

## 2. Access token must live in memory only

Current code:
- `persistAuthSession()` stores the access token in browser storage.
- The token is later read from the `localStorage` keys by the frontend helper chain.

Target state:
- Do not write the access token to browser storage.
- Keep a short-lived access token in React state or module memory only.
- On refresh/reload, force a `POST /auth/refresh` from the browser to the backend so the backend issues a new access token into memory.

Repository touchpoints:
- Current session file: `frontend/src/auth/session.ts`
- Current callback flow: `frontend/src/pages/Login/LoginCallbackPage.tsx`

## 3. Browser should carry an opaque session id cookie only

Current code:
- There is no `HttpOnly` session cookie flow in the repo yet.
- The front end currently receives Keycloak tokens and persists them through the browser helper.

Target state:
- On successful Keycloak authentication, the backend should set:
  - `session_id=<opaque-random-session-id>`
  - with flags: `HttpOnly`, `Secure`, `SameSite=Lax|Strict`, `Path=/`
- The browser should never receive a raw Keycloak refresh token or access token in storage.

Repository touchpoints to add:
- Backend route under `backend/app/api/routes/auth.py`
- New session model and session repository under `backend/app/db/models.py` or a dedicated session store

## 4. Session id maps to server-side storage

Current code:
- No server-side session store exists in the repo. The dependency layer is only header-driven.

Target state:
- Store a server-side record keyed by the session id:
  - `session_id`
  - `user_id`
  - `provider` (`keycloak`)
  - `refresh_token` or encrypted refresh token reference
  - `access_token` metadata or short-lived token reference
  - `issued_at`
  - `expires_at`
  - `revoked_at`
  - `rotation_version` or `family_id`
- Prefer Redis or a relational-backed table for a production session store.

Repository touchpoints:
- Existing session helper: `frontend/src/auth/session.ts`
- Existing auth dependency: `backend/app/dependencies/auth.py`
- Existing auth routes: `backend/app/api/routes/auth.py`

## 5. API token validation belongs in FastAPI middleware/dependency chain

Current code:
- The current backend authorization dependency is in `backend/app/dependencies/auth.py`.
- It reads headers and returns `CurrentUser`:
  - `user_id = request.headers.get("X-User-Id")`
  - `roles = request.headers.get("X-User-Role")`
  - `authenticated = bool(user_id and token)`
- This is only a scaffold demo and does not verify a real Keycloak JWT.
- The file says the pattern is intentionally database-free and route-agnostic.

Target state:
- Replace or extend `get_current_user()` so that it verifies:
  - the `Authorization: Bearer <access_token>` present on the request
  - the JWT signature using Keycloak JWKS
  - the `aud`, `iss`, `exp`, and claim groups
  - role mapping from the token
- The dependency should return `CurrentUser` only if the token passes the verification and the subject is known.

Repository touchpoints:
- `backend/app/dependencies/auth.py`
- `backend/app/api/routes/auth.py` exposes `/auth/me` and `/auth/keycloak/config`
- `backend/app/api/routes/*` depend on `require_authenticated_user` and `require_admin`

## 6. Backend refresh flow

Current code:
- No backend refresh route is present.
- No code path calls the Keycloak token endpoint with `grant_type=refresh_token`.
- No server-side refresh orchestration exists.

Target state:
- Add a backend route such as:
  - `POST /auth/refresh`
  - `POST /auth/logout`
- Refresh flow:
  1. Browser sends `Cookie: session_id=<opaque-value>` automatically.
  2. FastAPI reads the cookie.
  3. FastAPI resolves the session record in the DB/Redis store.
  4. FastAPI retrieves the server-side refresh token reference.
  5. FastAPI calls Keycloak’s token endpoint using `grant_type=refresh_token`.
  6. FastAPI returns a new short-lived access token into memory only.
  7. FastAPI rotates or updates the refresh token inside the server session record.

Repository touchpoints to add:
- `backend/app/api/routes/auth.py`
- `backend/app/dependencies/auth.py`
- DB or Redis session model/service

## 7. Backend logout and cookie revocation

Current code:
- `clearAuthSession()` in `frontend/src/auth/session.ts` removes entries from storage and removes the OAuth state.
- `getKeycloakLogoutUrl()` in `frontend/src/config/keycloak.ts` constructs a Keycloak logout URL with an optional `id_token_hint`.

Target state:
- On logout:
  1. Browser sends `POST /auth/logout`.
  2. Backend uses the session id from the cookie to invalidate the session record and revoke the refresh token reference.
  3. Backend clears the `HttpOnly` session cookie.
  4. Backend optionally also sends a logout request to the OIDC provider.

Repository touchpoints:
- `frontend/src/auth/session.ts` currently cleans only browser storage.
- `frontend/src/config/keycloak.ts` builds the Keycloak logout URL.

## 8. Authorization-code exchange should move behind the backend BFF

Current code:
- Frontend login callback page directly posts to Keycloak token endpoint using the authorization code.
- This code is in `frontend/src/pages/Login/LoginCallbackPage.tsx`.
- It receives `access_token`, `refresh_token`, and `id_token` directly.

Target state:
- Browser should redirect to Keycloak using Auth Code + PKCE.
- Backend should receive the callback (or an `/auth/callback` route), perform the code exchange with Keycloak, receive tokens, store the refresh token server-side, create the session cookie, and return a minimal success signal to the frontend.

Repository touchpoints:
- `frontend/src/pages/Login/LoginCallbackPage.tsx`
- `frontend/src/config/keycloak.ts`
- backend auth route structure in `backend/app/api/routes/auth.py`

## 9. CSRF and request-origin controls are mandatory with cookies

Current code:
- No CSRF handling exists in the repo.

Target state:
- Add CSRF/origin protection for all browser cookie-authenticated state-changing calls.
- Recommended controls:
  - `SameSite=Lax|Strict`
  - `Secure`
  - `HttpOnly`
  - `Origin`/`Referer` validation in FastAPI
  - state-changing endpoints should enforce an anti-CSRF token or double-submit pattern where needed

Repository touchpoints:
- Add middleware in `backend/app/main.py` or a dependency in `backend/app/dependencies/auth.py`

## 10. Refresh-token rotation and revocation

Current code:
- No refresh-token rotation or DB session record exists.

Target state:
- Store refresh tokens in a server-side session table.
- Rotate refresh token on each refresh request.
- Maintain one session family or `rotation_version` and revoke the prior token family on compromise.

Repository touchpoints:
- New session model
- New `POST /auth/refresh` route
- New `POST /auth/logout` route

## 11. Normalized implementation order

Recommended implementation sequence:

1. Replace the token-storing helper logic in `frontend/src/auth/session.ts` and stop writing tokens to browser storage.
2. Add a backend `POST /auth/logout` and `POST /auth/refresh` flow.
3. Build a server-side session model and `HttpOnly` session cookie generation.
4. Replace the header-only `get_current_user()` dependency with a real token validation dependency that verifies the Keycloak JWT and maps claims.
5. Move the Keycloak authorization-code exchange behind the backend BFF instead of the browser callback page.
6. Add CSRF/origin checks and token rotation.

## 12. Current repository evidence summary

Evidence currently in the repository:
- `frontend/src/pages/Login/LoginCallbackPage.tsx` exchanges the authorization code with Keycloak and receives the access/refresh/id tokens.
- `frontend/src/auth/session.ts` writes them to `localStorage` and removes them on logout.
- `backend/app/dependencies/auth.py` consumes header values and returns a `CurrentUser` object without real verification.
- `backend/app/api/routes/auth.py` publishes Keycloak endpoints and JWKS metadata but does not verify the token itself.

This is a scaffold and not yet a production authentication boundary.
