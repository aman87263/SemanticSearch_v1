export type DocumentStatus =
    | "uploading"
    | "processing"
    | "ready"
    | "failed";

export interface Document {
    id: string;          // UUID
    name: string;        // Original filename
    size: number;
    uploadedAt: Date;
    status: DocumentStatus;
    chunkCount?: number;

    fileHash?: string;   // Returned by backend
}