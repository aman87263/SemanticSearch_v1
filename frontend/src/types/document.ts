export type DocumentStatus =
    | "uploading"
    | "processing"
    | "completed"
    | "failed";

export interface Document {
    id: string;          // UUID
    name: string;        // Original filename
    size: number;
    uploadedAt: Date;
    status: DocumentStatus;
    chunkCount?: number;
    progress: number;
    fileHash?: string;   // Returned by backend
}