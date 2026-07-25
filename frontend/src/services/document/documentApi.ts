import { apiRequest } from "../http/httpClient";
import type { ApiResponse } from "../../types/api";
import type { Document } from "../../types/document";

export type UploadOutcome = "created" | "duplicate";

export interface UploadDocumentResponse {
    outcome: UploadOutcome;
    document: Document;
}

interface DocumentApiResponse {
    id: string;
    name: string;
    size: number;
    status: Document["status"];
    progress: number;
    processing_progress: number;
    uploadedAt: string;
    chunkCount?: number | null;
}

interface UploadDocumentApiResponse {
    outcome: UploadOutcome;
    document: DocumentApiResponse;
}

function mapDocument(document: DocumentApiResponse): Document {
    return {
        id: document.id,
        name: document.name,
        size: document.size,
        status: document.status,
        progress: document.progress,
        uploadedAt: new Date(document.uploadedAt),
        chunkCount: document.chunkCount ?? undefined,
    };
}

export async function getDocuments(): Promise<Document[]> {
    const response = await apiRequest<ApiResponse<DocumentApiResponse[]>>(
        "/documents"
    );

    return response.data?.map(mapDocument) ?? [];
}

export async function uploadDocuments(
    file: File
): Promise<UploadDocumentResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await apiRequest<ApiResponse<UploadDocumentApiResponse>>(
        "/documents",
        {
            method: "POST",
            body: formData,
        }
    );

    if (!response.data) {
        throw new Error("Upload response did not include document data.");
    }

    return {
        outcome: response.data.outcome,
        document: mapDocument(response.data.document),
    };
}

export async function deleteDocument(
    documentId: string
): Promise<boolean> {
    const response = await apiRequest<ApiResponse<boolean>>(
        `/documents/${documentId}`,
        {
            method: "DELETE",
        }
    );

    return response.data ?? false;
}
