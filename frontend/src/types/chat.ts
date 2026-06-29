export interface MessageSource {
    documentName: string;
    pageNumber?: number;
}
export interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    createdAt: Date;
    sources?: MessageSource[];
}