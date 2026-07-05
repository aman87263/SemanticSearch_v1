import type { Document } from "../types/document";
import { createContext, useState } from "react";
import * as documentService from "../services/documentService";
import { delay } from "../services/documentService";

export interface DocumentContextType {
    documents: Document[];
    loading: boolean;

    uploadDocument(file: File): Promise<void>;
    deleteDocument(id: string): Promise<void>;
    refreshDocuments(): Promise<void>;
}

export const DocumentContext = createContext<DocumentContextType | undefined>(undefined);

interface DocumentProviderProps {
    children: React.ReactNode;
}

export function DocumentProvider({
    children,
}: DocumentProviderProps) {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(false);
    function updateDocument(
        id: string,
        updates: Partial<Document>
    ) {
        setDocuments(prev =>
            prev.map(doc =>
                doc.id === id
                    ? { ...doc, ...updates }
                    : doc
            )
        );
    }
    async function uploadDocument(file: File): Promise<void> {
        setLoading(true);

        try {
            // Upload the file (currently mocked)
            const document = await documentService.uploadDocument(file);

            // Add it to the UI immediately
            setDocuments(prev => [...prev, document]);

            // Simulate upload progress
            await simulateUploadProgress(document.id);

            // Backend starts processing
            updateDocument(document.id, {
                status: "processing",
                progress: 100,
            });

            // Simulate embedding/chunking work
            await simulateProcessing(document.id);

        } catch (error) {
            console.error("Upload failed", error);
        } finally {
            setLoading(false);
        }
    }
    async function deleteDocument(id: string) {
        setDocuments(prev =>
            prev.filter(doc => doc.id !== id)
        );
    }
    async function refreshDocuments() {
        // Later:
        // const docs = await documentService.getDocuments();
        // setDocuments(docs);
    }
    async function simulateUploadProgress(
        documentId: string
    ) {

        for (let progress = 0; progress <= 100; progress += 10) {

            updateDocument(documentId, {
                progress,
            });

            await delay(200);
        }

    }
    async function simulateProcessing(
        documentId: string
    ): Promise<void> {

        await delay(2000);

        updateDocument(documentId, {
            status: "ready",
            progress: 100,
            chunkCount: Math.floor(Math.random() * 150) + 50,
        });
    }
    return (
        <DocumentContext.Provider
            value={{
                documents,
                loading,
                uploadDocument,
                deleteDocument,
                refreshDocuments,
            }}
        >
            {children}
        </DocumentContext.Provider>
    );
}