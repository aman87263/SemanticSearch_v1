const OAUTH_STATE_KEY = "semanticsearch_oauth_state";

let inMemoryAccessToken: string | null = null;

export function getAccessToken(): string | null {
    return inMemoryAccessToken;
}

export function setAccessToken(token: string | null): void {
    inMemoryAccessToken = token;
}

export function hasAuthToken(): boolean {
    return Boolean(inMemoryAccessToken);
}

export function getStoredIdToken(): string | null {
    return null;
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
    userId: string;
    roles: string[];
    provider: string;
}

export function persistAuthSession(session: AuthSessionPayload): void {
    // Store session payload in memory only, not in browser storage
    // The access token should already be set by the frontend callback handler
    // This function is kept for backward compatibility but should be a no-op
    // for token storage as per the security implementation plan
    void session;
    // No browser storage operations - tokens should only live in memory
}

export function clearAuthSession(): void {
    setAccessToken(null);
    // No localStorage removal - tokens should not be stored there
    sessionStorage.removeItem(OAUTH_STATE_KEY);
    // Notify auth change
    notifyAuthChanged();
}

export function notifyAuthChanged(): void {
    window.dispatchEvent(new Event("auth-changed"));
}
