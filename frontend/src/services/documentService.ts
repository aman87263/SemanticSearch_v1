import type { Document } from "../types/document";
import {
    uploadDocuments,
    getDocuments as getDocumentsFromApi,
    deleteDocument as deleteDocumentFromApi,
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
    file: File
): Promise<UploadDocumentResponse> {
    return uploadDocuments(file);
}

export async function deleteDocument(
    documentId: string
): Promise<boolean> {
    return deleteDocumentFromApi(documentId);
}
