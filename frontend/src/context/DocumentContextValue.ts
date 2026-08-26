import { createContext } from "react";

import type { Document } from "../types/document";

export interface DocumentContextType {
    documents: Document[];
    loading: boolean;
    uploadDocument(file: File): Promise<void>;
    deleteDocument(id: string): Promise<void>;
    refreshDocuments(): Promise<void>;
}

export const DocumentContext = createContext<DocumentContextType | undefined>(undefined);
