import type { Document } from "../types/document";
import { createContext, useEffect, useState } from "react";
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
    useEffect(() => {
        refreshDocuments();
    }, []);
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
            const result = await documentService.uploadDocument(file);

            // Add it to the UI immediately
            setDocuments((prev) => {
                const exists = prev.some(
                    (d) => d.id === result.document.id
                );

                if (exists) {
                    return prev;
                }

                return [result.document, ...prev];
            });
            // Simulate upload progress
            await simulateUploadProgress(result.document.id);

            // Backend starts processing
            updateDocument(result.document.id, {
                status: "processing",
                progress: 100,
            });

            // Simulate embedding/chunking work
            await simulateProcessing(result.document.id);

        } catch (error) {
            console.error("Upload failed", error);
        } finally {
            setLoading(false);
        }
    }
    const deleteDocument = async (id: string) => { // Keep previous state in case API fails 
        const previousDocuments = documents;
        //Optimistic UI update 
        setDocuments((prev) => prev.filter((d) => d.id !== id));
        try {
            const deleted = await documentService.deleteDocument(id);
            if (!deleted) { // Restore state if backend says nothing was deleted 
                setDocuments(previousDocuments);
                throw new Error("Document not found");
            }
        }
        catch (error) { // Rollback on failure 
            setDocuments(previousDocuments);
            console.error(error);
            throw error;
        }
    };
    async function refreshDocuments() {
        try {
            const documents = await documentService.getDocuments();
            setDocuments(documents);
        } catch (error) {
            console.error(error);
        }
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