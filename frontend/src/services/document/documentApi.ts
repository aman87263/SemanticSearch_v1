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
    uploader_email?: string;
    uploader_name?: string;
    visibility: "PRIVATE" | "PUBLIC";
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
        uploaderEmail: document.uploader_email,
        uploaderName: document.uploader_name,
        visibility: document.visibility,
    };
}

export async function getDocuments(): Promise<Document[]> {
    const response = await apiRequest<ApiResponse<DocumentApiResponse[]>>(
        "/documents"
    );
    // console.log("getDocuments response:", response.data?.map(mapDocument));
    return response.data?.map(mapDocument) ?? [];
}

export async function uploadDocuments(
    file: File,
    visibility: "PRIVATE" | "PUBLIC" = "PRIVATE"
): Promise<UploadDocumentResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("visibility", visibility);

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

export async function updateDocumentVisibility(
    documentId: string,
    visibility: "PRIVATE" | "PUBLIC"
): Promise<Document> {
    const response = await apiRequest<ApiResponse<DocumentApiResponse>>(
        `/documents/${documentId}/visibility`,
        {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ visibility }),
        }
    );

    if (!response.data) {
        throw new Error("Update visibility response did not include document data.");
    }

    return mapDocument(response.data);
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
