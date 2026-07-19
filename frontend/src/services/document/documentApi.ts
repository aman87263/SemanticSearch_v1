import { apiRequest } from "../http/httpClient";
import type { ApiResponse } from "../../types/api";
import type { Document } from "../../types/document";

export type UploadOutcome = "created" | "duplicate";
const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL;

export interface UploadDocumentResponse {
    outcome: UploadOutcome;
    document: Document;
}

export async function getDocuments(): Promise<Document[]> {
    const response = await fetch(
        `${API_BASE_URL}/documents`
    );

    if (!response.ok) {
        throw new Error(
            `Failed to load documents: ${response.status}`
        );
    }

    const data =
        (await response.json()) as ApiResponse<Document[]>;

    return data.data;
}

export async function uploadDocuments(
    file: File
): Promise<UploadDocumentResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(
        `${API_BASE_URL}/documents`,
        {
            method: "POST",
            body: formData,
        }
    );

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
            `Upload failed: ${response.status} ${errorText}`
        );
    }
    const data =
        (await response.json()) as ApiResponse<UploadDocumentResponse>;

    return data.data;
}
export async function deleteDocument(
    documentId: string
): Promise<boolean> {
    const response = await fetch(
        `${API_BASE_URL}/documents/${documentId}`,
        {
            method: "DELETE",
        }
    );

    if (!response.ok) {
        throw new Error(
            `Delete failed: ${response.status}`
        );
    }

    const data =
        (await response.json()) as ApiResponse<boolean>;

    return data.data;
}