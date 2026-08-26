import { useContext } from "react";
import { DocumentContext } from "../context/DocumentContextValue";

export function useDocuments() {
    const context = useContext(DocumentContext);

    if (!context) {
        throw new Error(
            "useDocuments must be used inside DocumentProvider"
        );
    }

    return context;
}