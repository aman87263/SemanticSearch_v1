Yes — **the plan is substantially better than the current `localStorage` design**, and it is moving your application toward a proper **BFF-style authentication architecture**.

However, there are **2–3 important corrections I'd make before implementing it**. One of them is architectural.

## 1. What your proposed architecture becomes

Your current architecture is effectively:

```text
React
  │
  │ access_token
  ▼
FastAPI
```

with:

```text
access_token
refresh_token
id_token
       ↓
localStorage
```

The proposed architecture becomes:

```text
                         ┌─────────────┐
                         │  Keycloak   │
                         └──────▲──────┘
                                │
                           OAuth/OIDC
                                │
                                │
┌──────────────┐          ┌─────┴──────┐
│    React     │          │   FastAPI  │
│     SPA      │◄────────►│    BFF     │
└──────┬───────┘          └─────┬──────┘
       │                        │
       │ HttpOnly cookie        │
       │                        │
       │ access token in        │
       │ memory only            │
       │                        │
       └────────────────────────┘
```

That's a **good direction**.

---

# 2. One important correction: don't necessarily put the Keycloak refresh token in the browser cookie

Your plan says:

> Backend should set the refresh token as an HttpOnly cookie.

That's certainly much safer than localStorage because JavaScript can't read it.

But for an enterprise application, I'd actually consider going one step further:

### Better

Instead of:

```text
Browser
   │
   │ HttpOnly cookie
   │ containing Keycloak refresh token
   ▼
FastAPI
   │
   ▼
Keycloak
```

consider:

```text
Browser
   │
   │ HttpOnly cookie
   │ containing opaque session ID
   ▼
FastAPI
   │
   │ session ID
   ▼
Redis / DB
   │
   ├── Keycloak refresh token
   ├── user ID
   ├── session metadata
   └── expiry
```

So the browser only possesses:

```text
session_id = random opaque value
```

and **never possesses a Keycloak refresh token at all**.

This gives you:

```text
Browser
   ↓
HttpOnly session cookie
   ↓
FastAPI
   ↓
server-side session
   ↓
Keycloak refresh token
```

That's a stronger BFF architecture.

For your AI Knowledge Platform, I'd favor this if you're deliberately building it as a production-grade enterprise project.

---

# 3. Your proposed access-token-in-memory approach is good

This part is good:

> Keep the access token in memory only.

For example:

```ts
let accessToken: string | null = null;
```

Then:

```text
React
   │
   │ accessToken from memory
   ▼
FastAPI
```

If someone refreshes the browser:

```text
Browser refresh
      ↓
JavaScript memory destroyed
      ↓
accessToken = null
      ↓
POST /auth/refresh
      ↓
HttpOnly cookie automatically sent
      ↓
FastAPI
      ↓
Keycloak
      ↓
new access token
      ↓
React memory
```

This is exactly the behavior you want.

---

# 4. And this answers your earlier question about "automatic refresh"

With this architecture, **you explicitly implement it**.

For example:

```text
Application starts
       │
       ▼
accessToken = null
       │
       ▼
POST /auth/refresh
       │
       │ browser automatically
       │ sends HttpOnly cookie
       ▼
FastAPI
       │
       ▼
Keycloak
       │
       ▼
new access token
       │
       ▼
React memory
```

Then API calls use:

```http
Authorization: Bearer <access_token>
```

So your frontend doesn't need to know the refresh token.

---

# 5. But there's a major architectural question about `/login`

Your plan says:

```text
POST /login
```

I'd be careful here.

You **don't want FastAPI to receive the user's Keycloak username/password**.

The browser should still redirect the user to Keycloak:

```text
React
  │
  │ Authorization Code + PKCE
  ▼
Keycloak
  │
  │ login
  ▼
Keycloak
  │
  │ authorization code
  ▼
React / callback
```

Then, for a true BFF, I'd preferably have the **backend handle the code exchange**:

```text
React
   │
   │ authorization request
   ▼
Keycloak
   │
   │ authorization code
   ▼
FastAPI callback
   │
   │ code exchange
   ▼
Keycloak /token
   │
   ├── access token
   ├── refresh token
   └── ID token
   │
   ▼
FastAPI
   │
   ├── store refresh token server-side
   ├── establish session
   └── Set-Cookie: session=...
   │
   ▼
React
```

That's a very clean architecture.

---

# 6. The ideal architecture I'd recommend for your project

I'd actually modify the plan to this:

```text
                         ┌─────────────┐
                         │  Keycloak   │
                         └──────▲──────┘
                                │
                         Authorization
                           Code + PKCE
                                │
                                │
                         ┌──────┴──────┐
                         │   FastAPI   │
                         │     BFF     │
                         └──────┬──────┘
                                │
                         Server-side
                           session
                                │
                         ┌──────▼──────┐
                         │ Redis / DB  │
                         │             │
                         │ refresh_token
                         │ user_id     │
                         │ expiry      │
                         └─────────────┘
                                ▲
                                │
                      HttpOnly session cookie
                                │
                                │
                         ┌──────┴──────┐
                         │    React    │
                         │     SPA     │
                         └─────────────┘
```

Then your browser has:

```text
HttpOnly
Secure
SameSite=Lax/Strict
session=<opaque-random-value>
```

but **not**:

```text
access_token
refresh_token
id_token
```

in browser storage.

---

# 7. What happens when the access token expires?

This becomes very clean.

Suppose:

```text
Access token = 5 minutes
Session = longer lived
```

At 5 minutes:

```text
React
  │
  │ API call
  ▼
FastAPI
  │
  │ access token expired
  ▼
401
```

Your frontend can call:

```http
POST /auth/refresh
```

The browser automatically sends:

```http
Cookie: session=abc123
```

FastAPI:

```text
session=abc123
      ↓
lookup session
      ↓
retrieve Keycloak refresh token
      ↓
Keycloak /token
      ↓
new access token
      ↓
update server-side session
      ↓
return access token
```

React puts the new access token **only in memory**.

---

# 8. Your roles approach is also correct

You said:

> Don't persist roles in localStorage.

Correct.

The backend should ultimately make the authorization decision.

For example:

```text
JWT
 │
 ├── sub = user123
 ├── roles = ["user"]
 └── ...
       │
       ▼
FastAPI
       │
       ▼
Is user allowed to delete document?
       │
    ┌──┴───┐
   YES     NO
    │       │
   200     403
```

React can still use user/role information for **UI rendering**:

```text
if role === "admin":
    show Admin button
```

but that is only UX.

The backend remains the authority.

---

# 9. One thing I'd change in the plan's cookie wording

It says:

> short expiry

for the refresh-token cookie.

I'd avoid prescribing that without deciding your session model.

A refresh token is normally **longer-lived than an access token**.

For example, conceptually:

```text
Access token
──────────────
5–15 minutes

Refresh/session
────────────────────────────
hours/days/etc.
```

The exact lifetime should be determined by your security requirements and Keycloak configuration.

If you use an opaque server-side session cookie, you can make the browser session lifetime independently manageable.

---

# 10. CSRF is important — but understand where it applies

Once authentication relies on cookies, browsers automatically attach those cookies to requests.

Therefore you need to think about CSRF.

For your architecture:

```text
React
   │
   │ POST /auth/refresh
   │ Cookie automatically attached
   ▼
FastAPI
```

and especially for state-changing endpoints:

```text
POST /documents
DELETE /documents/123
POST /chat
```

you need appropriate CSRF/origin protections.

For a same-origin SPA + API setup, you can combine:

- `SameSite=Lax` or `Strict` where compatible
- strict CORS
- Origin checking
- CSRF token for state-changing operations where appropriate

Don't simply rely on CORS as your CSRF defense.

---

# 11. So I'd rate the proposed plan

| Part | My assessment |
|---|---|
| Remove tokens from `localStorage` | ✅ Absolutely |
| Access token only in memory | ✅ Good |
| HttpOnly + Secure cookie | ✅ Good |
| Backend `/refresh` | ✅ Good |
| Backend `/logout` | ✅ Good |
| Backend validates authorization | ✅ Absolutely |
| Don't trust localStorage roles | ✅ Correct |
| CSRF protection | ✅ Required consideration |
| SPA + FastAPI BFF | ⭐ Very good |
| Browser stores raw Keycloak refresh token | ⚠️ Safe improvement, but can be improved further |
| Server-side session + opaque cookie | ⭐ **My preferred design** |

### My recommendation

For your project, I'd build:

```text
              KEYCLOAK
                  ▲
                  │
          OAuth/OIDC + PKCE
                  │
                  ▼
               FASTAPI
                BFF
                  │
         ┌────────┴────────┐
         │                 │
    session store      your APIs
     Redis/DB
         │
   refresh token
         │
         ▼
      Keycloak


React SPA
    │
    │ HttpOnly session cookie
    ▼
  FastAPI
```

**No access token, refresh token, or ID token in `localStorage`.**

And ideally:

**No raw Keycloak refresh token in the browser at all.**

That would make the authentication portion of your AI Knowledge Platform much more representative of an enterprise architecture rather than simply making the existing implementation slightly safer.