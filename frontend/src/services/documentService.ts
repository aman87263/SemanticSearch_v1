import type { Document } from "../types/document";


export const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export async function uploadDocument(file: File): Promise<Document> {

    await delay(1000);

    return {
        id: crypto.randomUUID(),
        name: file.name,
        size: file.size,
        uploadedAt: new Date(),
        status: "uploading",
        progress: 0,
    };
}