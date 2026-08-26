export interface SearchResult {
    id: string;
    document_id: string;
    document_name: string | null;
    index: number;
    text: string;
    token_count: number;
    metadata: Record<string, unknown>;
    similarity: number;
    rerank_score: number | null;
}

export interface SearchResponse {
    results: SearchResult[];
}
