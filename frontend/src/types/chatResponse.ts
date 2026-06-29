import type { MessageSource } from "./chat";

export interface ChatResponse {
    content: string;
    sources?: MessageSource[];
}