import { createOAuthState, getStoredIdToken } from "../auth/session";

function readEnv(name: string, viteName: string, fallback: string): string {
  const value =
    (import.meta.env[name] as string | undefined) ||
    (import.meta.env[viteName] as string | undefined);

  return value?.trim() ? value : fallback;
}

const redirectUri = readEnv(
  "KEYCLOAK_REDIRECT_URI",
  "VITE_KEYCLOAK_REDIRECT_URI",
  "http://localhost:5173/login/callback"
);

function resolveLogoutRedirectUri(loginRedirectUri: string): string {
  const explicit = readEnv(
    "KEYCLOAK_POST_LOGOUT_REDIRECT_URI",
    "VITE_KEYCLOAK_POST_LOGOUT_REDIRECT_URI",
    ""
  );

  if (explicit) {
    return explicit;
  }

  try {
    const url = new URL(loginRedirectUri);
    url.pathname = "/login";
    url.search = "";
    url.hash = "";
    return url.toString();
  } catch {
    return "http://localhost:5173/login";
  }
}

export const keycloakConfig = {
  url: readEnv("KEYCLOAK_URL", "VITE_KEYCLOAK_URL", "http://localhost:9090"),
  realm: readEnv("KEYCLOAK_REALM", "VITE_KEYCLOAK_REALM", "semanticsearch"),
  clientId: readEnv(
    "KEYCLOAK_CLIENT_ID",
    "VITE_KEYCLOAK_CLIENT_ID",
    "semanticsearch-web"
  ),
  redirectUri,
  logoutRedirectUri: resolveLogoutRedirectUri(redirectUri),
  scope: readEnv(
    "KEYCLOAK_SCOPE",
    "VITE_KEYCLOAK_SCOPE",
    "openid profile email"
  ),
};

export function getKeycloakLoginUrl() {
  const state = createOAuthState();
  const params = new URLSearchParams({
    client_id: keycloakConfig.clientId,
    redirect_uri: keycloakConfig.redirectUri,
    response_type: "code",
    scope: keycloakConfig.scope,
    state,
  });

  return `${keycloakConfig.url}/realms/${keycloakConfig.realm}/protocol/openid-connect/auth?${params.toString()}`;
}

export function getKeycloakLogoutUrl(idTokenHint?: string | null) {
  const idToken = idTokenHint ?? getStoredIdToken();
  const params = new URLSearchParams({
    client_id: keycloakConfig.clientId,
    post_logout_redirect_uri: keycloakConfig.logoutRedirectUri,
  });

  if (idToken) {
    params.set("id_token_hint", idToken);
  }

  return `${keycloakConfig.url}/realms/${keycloakConfig.realm}/protocol/openid-connect/logout?${params.toString()}`;
}

export function redirectToKeycloakLogin() {
  window.location.assign(getKeycloakLoginUrl());
}
