export type MessageRole = "user" | "assistant";

export interface Citation {
    document_id: string;
    document_name: string | null;
    chunk_id: string;
    chunk_index: number;
    similarity: number | null;
    rerank_score: number | null;
}

export interface Message {
    id: string;
    role: MessageRole;
    content: string;
    createdAt: Date;
    citations?: Citation[];
}

export interface ChatResponse {
    answer: string;
    citations: Citation[];
}
