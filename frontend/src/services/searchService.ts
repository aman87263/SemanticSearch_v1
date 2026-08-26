import { apiRequest } from "./http/httpClient";
import type { SearchResponse } from "../types/search";

export async function searchDocuments(
    query: string,
    documentId?: string,
): Promise<SearchResponse> {
    return apiRequest<SearchResponse>("/search", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            query,
            document_id: documentId,
        }),
    });
}
