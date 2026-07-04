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
            // 1. Upload (currently mock service)
            const document = await documentService.uploadDocument(file);

            // 2. Add document to the list
            setDocuments(prev => [...prev, document]);

            // 3. Simulate backend processing
            await delay(1500);

            updateDocument(document.id, {
                status: "processing",
            });

            // 4. Simulate embedding completion
            await delay(2000);

            updateDocument(document.id, {
                status: "ready",
                chunkCount: Math.floor(Math.random() * 150) + 50,
            });
        } catch (error) {
            console.error(error);
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