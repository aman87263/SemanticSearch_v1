const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export async function apiRequest<T>(
    input: string,
    init?: RequestInit
): Promise<T> {
    const response = await fetch(
        `${API_BASE_URL}${input}`,
        init
    );

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
            `API Error ${response.status}: ${errorText}`
        );
    }

    return response.json() as Promise<T>;
}
