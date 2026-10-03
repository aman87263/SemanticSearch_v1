import { useEffect, useState } from "react";
import * as documentService from "../services/documentService";
import type { Document } from "../types/document";
import { DocumentContext } from "./DocumentContextValue";
import { useAuth } from "../hooks/useAuth";

interface DocumentProviderProps {
    children: React.ReactNode;
}

export function DocumentProvider({
    children,
}: DocumentProviderProps) {
    const { isAuthenticated } = useAuth();
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!isAuthenticated) {
            return;
        }

        refreshDocuments().then(() => {
            // refreshDocuments handles its own setDocuments
        });
    }, [isAuthenticated]);

    // Clear documents when logged out
    useEffect(() => {
        if (!isAuthenticated) {
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setDocuments([]);
        }
    }, [isAuthenticated]);

    async function uploadDocument(
        file: File,
        visibility: "PRIVATE" | "PUBLIC" = "PRIVATE"
    ): Promise<void> {
        setLoading(true);

        try {
            const result = await documentService.uploadDocument(file, visibility);

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

    const updateDocumentVisibility = async (
        documentId: string,
        visibility: "PRIVATE" | "PUBLIC"
    ) => {
        const previousDocuments = documents;

        setDocuments((prev) =>
            prev.map((document) =>
                document.id === documentId
                    ? { ...document, visibility }
                    : document
            )
        );

        try {
            const updatedDoc = await documentService.updateDocumentVisibility(
                documentId,
                visibility
            );

            setDocuments((prev) =>
                prev.map((document) =>
                    document.id === documentId ? updatedDoc : document
                )
            );
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
                updateDocumentVisibility,
                refreshDocuments,
            }}
        >
            {children}
        </DocumentContext.Provider>
    );
}
