export type MessageRole = "user" | "assistant";

export interface MessageSource {
    documentName: string;
    pageNumber?: number;
}

export interface Message {
    id: string;
    role: MessageRole;
    content: string;
    createdAt: Date;
    sources?: MessageSource[];
}

export interface ChatResponse {
    content: string;
    sources?: MessageSource[];
}