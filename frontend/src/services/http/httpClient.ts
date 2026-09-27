import { getAccessToken } from "../../auth/session";


const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

interface ApiErrorResponse {
    success?: boolean;
    error?: {
        code: string;
        message: string;
    };
}

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
            credentials: "include",
        }
    );

    if (!response.ok) {
        let friendlyMessage = `Request failed with status ${response.status}`;
        
        try {
            const errorData = await response.json() as ApiErrorResponse;
            if (errorData.error?.message) {
                friendlyMessage = errorData.error.message;
            } else if (errorData.error?.code) {
                // Map common error codes to friendly messages
                const codeMessages: Record<string, string> = {
                    "SESSION_INVALID": "Your session has expired. Please log in again.",
                    "SESSION_EXPIRED": "Your session has expired. Please log in again.",
                    "INVALID_FILE_TYPE": "This file type is not supported.",
                    "FILE_TOO_LARGE": "File is too large. Maximum size is 10MB.",
                    "DUPLICATE_DOCUMENT": "This document has already been uploaded.",
                    "DOCUMENT_NOT_FOUND": "Document not found.",
                    "UNAUTHORIZED": "You are not authorized to perform this action.",
                    "FORBIDDEN": "You don't have permission to access this resource.",
                };
                friendlyMessage = codeMessages[errorData.error.code] || errorData.error.code;
            }
        } catch {
            // If parsing fails, use the status text
            friendlyMessage = response.statusText || friendlyMessage;
        }
        
        throw new Error(friendlyMessage);
    }

    return response.json() as Promise<T>;
}
