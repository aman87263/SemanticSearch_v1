import { getAccessToken } from "../../auth/session";

const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export async function apiRequest<T>(
    input: string,
    init?: RequestInit
): Promise<T> {
    const headers = new Headers(init?.headers ?? {});

    const accessToken = getAccessToken();
    if (accessToken) {
        headers.set("Authorization", `Bearer ${accessToken}`);
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
