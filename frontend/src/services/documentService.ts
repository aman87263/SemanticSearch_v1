import type { Document } from "../types/document";
import {
    uploadDocuments,
    getDocuments as getDocumentsFromApi,
    deleteDocument as deleteDocumentFromApi,
    updateDocumentVisibility as updateDocumentVisibilityApi,
} from "./document/documentApi";

export type UploadOutcome = "created" | "duplicate";

export interface UploadDocumentResponse {
    outcome: UploadOutcome;
    document: Document;
}

export async function getDocuments(): Promise<Document[]> {
    return getDocumentsFromApi();
}

export async function uploadDocument(
    file: File,
    visibility: "PRIVATE" | "PUBLIC" = "PRIVATE"
): Promise<UploadDocumentResponse> {
    return uploadDocuments(file, visibility);
}

export async function deleteDocument(
    documentId: string
): Promise<boolean> {
    return deleteDocumentFromApi(documentId);
}

export async function updateDocumentVisibility(
    documentId: string,
    visibility: "PRIVATE" | "PUBLIC"
): Promise<Document> {
    return updateDocumentVisibilityApi(documentId, visibility);
}
