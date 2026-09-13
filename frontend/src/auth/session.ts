const ACCESS_TOKEN_KEY = "semanticsearch_access_token";
const REFRESH_TOKEN_KEY = "semanticsearch_refresh_token";
const ID_TOKEN_KEY = "semanticsearch_id_token";
const USER_ID_KEY = "semanticsearch_user_id";
const USER_ROLES_KEY = "semanticsearch_user_roles";
const PROVIDER_KEY = "semanticsearch_provider";
const OAUTH_STATE_KEY = "semanticsearch_oauth_state";

export function hasAuthToken(): boolean {
    return Boolean(localStorage.getItem(ACCESS_TOKEN_KEY));
}

export function getStoredIdToken(): string | null {
    return localStorage.getItem(ID_TOKEN_KEY);
}

export function createOAuthState(): string {
    const state = crypto.randomUUID();
    sessionStorage.setItem(OAUTH_STATE_KEY, state);
    return state;
}

export function isOAuthStateValid(received: string | null): boolean {
    const expected = sessionStorage.getItem(OAUTH_STATE_KEY);

    if (!expected || !received) {
        return false;
    }

    return expected === received;
}

export function clearOAuthState(): void {
    sessionStorage.removeItem(OAUTH_STATE_KEY);
}

export interface AuthSessionPayload {
    accessToken: string;
    refreshToken?: string;
    idToken?: string;
    userId: string;
    roles: string[];
    provider: string;
}

export function persistAuthSession(session: AuthSessionPayload): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, session.accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, session.refreshToken ?? "");
    localStorage.setItem(ID_TOKEN_KEY, session.idToken ?? "");
    localStorage.setItem(USER_ID_KEY, session.userId);
    localStorage.setItem(USER_ROLES_KEY, session.roles.join(","));
    localStorage.setItem(PROVIDER_KEY, session.provider);
}

export function clearAuthSession(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(ID_TOKEN_KEY);
    localStorage.removeItem(USER_ID_KEY);
    localStorage.removeItem(USER_ROLES_KEY);
    localStorage.removeItem(PROVIDER_KEY);
    sessionStorage.removeItem(OAUTH_STATE_KEY);
}

export function notifyAuthChanged(): void {
    window.dispatchEvent(new Event("auth-changed"));
}
