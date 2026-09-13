const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export async function apiRequest<T>(
    input: string,
    init?: RequestInit
): Promise<T> {
    const headers = new Headers(init?.headers ?? {});

    const accessToken = localStorage.getItem("semanticsearch_access_token");
    if (accessToken) {
        headers.set("Authorization", `Bearer ${accessToken}`);
    }

    const userId = localStorage.getItem("semanticsearch_user_id");
    if (userId) {
        headers.set("X-User-Id", userId);
    }

    const roles = localStorage.getItem("semanticsearch_user_roles");
    if (roles) {
        headers.set("X-User-Role", roles);
    }

    const provider = localStorage.getItem("semanticsearch_provider");
    if (provider) {
        headers.set("X-Identity-Provider", provider);
    }

    const response = await fetch(
        `${API_BASE_URL}${input}`,
        {
            ...init,
            headers,
        }
    );

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
            `API Error ${response.status}: ${errorText}`
        );
    }

    return response.json() as Promise<T>;
}
