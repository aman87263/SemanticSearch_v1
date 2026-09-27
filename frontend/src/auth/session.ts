const OAUTH_STATE_KEY = "semanticsearch_oauth_state";
const PKCE_CODE_VERIFIER_KEY = "semanticsearch_pkce_code_verifier";

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

/**
 * Generates a PKCE code_verifier as per RFC 7636.
 * Returns a cryptographically random string between 43-128 characters.
 */
export function generateCodeVerifier(): string {
    // Generate 32 bytes (256 bits) of random data
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    // Base64url encode (no padding, URL-safe)
    return btoa(String.fromCharCode(...array))
        .replace(/\+/g, "-")
        .replace(/\//g, "_")
        .replace(/=/g, "");
}

/**
 * Generates a PKCE code_challenge from a code_verifier using SHA-256 (S256 method).
 */
export async function generateCodeChallenge(codeVerifier: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(codeVerifier);
    const digest = await crypto.subtle.digest("SHA-256", data);
    // Base64url encode the hash
    return btoa(String.fromCharCode(...new Uint8Array(digest)))
        .replace(/\+/g, "-")
        .replace(/\//g, "_")
        .replace(/=/g, "");
}

/**
 * Stores the PKCE code_verifier in sessionStorage.
 */
export function setCodeVerifier(codeVerifier: string): void {
    sessionStorage.setItem(PKCE_CODE_VERIFIER_KEY, codeVerifier);
}

/**
 * Retrieves and removes the PKCE code_verifier from sessionStorage.
 */
export function consumeCodeVerifier(): string | null {
    const codeVerifier = sessionStorage.getItem(PKCE_CODE_VERIFIER_KEY);
    if (codeVerifier) {
        sessionStorage.removeItem(PKCE_CODE_VERIFIER_KEY);
    }
    return codeVerifier;
}

/**
 * Checks if a PKCE code_verifier exists in sessionStorage.
 */
export function hasCodeVerifier(): boolean {
    return sessionStorage.getItem(PKCE_CODE_VERIFIER_KEY) !== null;
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

const API_BASE_URL =
    (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
    "/api";

export async function restoreSession(): Promise<boolean> {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
            method: "POST",
            credentials: "include",
        });

        if (!response.ok) {
            return false;
        }

        const data = await response.json();
        if (data.success && data.data?.access_token) {
            setAccessToken(data.data.access_token);
            notifyAuthChanged();
            return true;
        }
        return false;
    } catch {
        return false;
    }
}
