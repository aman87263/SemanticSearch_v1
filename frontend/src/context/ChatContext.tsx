import {
    createContext,
    useContext,
    useState,
    type ReactNode,
} from "react";

import { sendMessage as sendMessageToAI } from "../services/chatService";
import type { ChatResponse, Message } from "../types/chat";

interface ChatContextType {
    messages: Message[];
    loading: boolean;
    sendMessage: (text: string) => Promise<void>;
}

export const ChatContext = createContext<ChatContextType | undefined>(undefined);

interface ChatProviderProps {
    children: ReactNode;
}

export function ChatProvider({
    children,
}: ChatProviderProps) {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: crypto.randomUUID(),
            role: "assistant",
            content: "Hi 👋 Ask me anything from your documents.",
            createdAt: new Date(),
        },
    ]);

    const [loading, setLoading] = useState(false);

    async function sendMessage(text: string) {
        const userMessage: Message = {
            id: crypto.randomUUID(),
            role: "user",
            content: text,
            createdAt: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);

        setLoading(true);

        try {
            const response: ChatResponse = await sendMessageToAI(text);

            const assistantMessage: Message = {
                id: crypto.randomUUID(),
                role: "assistant",
                content: response.content,
                createdAt: new Date(),
                sources: response.sources,
            };

            setMessages((prev) => [...prev, assistantMessage]);
        } finally {
            setLoading(false);
        }
    }

    return (
        <ChatContext.Provider
            value={{
                messages,
                loading,
                sendMessage,
            }}
        >
            {children}
        </ChatContext.Provider>
    );
}

