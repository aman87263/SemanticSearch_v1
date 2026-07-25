import type { Document } from "../types/document";
import { createContext, useEffect, useState } from "react";
import * as documentService from "../services/documentService";

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

    async function uploadDocument(file: File): Promise<void> {
        setLoading(true);

        try {
            const result = await documentService.uploadDocument(file);

            setDocuments((prev) => {
                const exists = prev.some(
                    (document) => document.id === result.document.id
                );

                if (exists) {
                    return prev.map((document) =>
                        document.id === result.document.id
                            ? result.document
                            : document
                    );
                }

                return [result.document, ...prev];
            });
        } catch (error) {
            console.error("Upload failed", error);
            throw error;
        } finally {
            setLoading(false);
        }
    }

    const deleteDocument = async (id: string) => {
        const previousDocuments = documents;

        setDocuments((prev) => prev.filter((document) => document.id !== id));

        try {
            const deleted = await documentService.deleteDocument(id);

            if (!deleted) {
                setDocuments(previousDocuments);
                throw new Error("Document not found");
            }
        } catch (error) {
            setDocuments(previousDocuments);
            console.error(error);
            throw error;
        }
    };

    async function refreshDocuments() {
        try {
            const loadedDocuments = await documentService.getDocuments();
            setDocuments(loadedDocuments);
        } catch (error) {
            console.error(error);
        }
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
