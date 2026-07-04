import {
    createContext,
    useState,
    type ReactNode
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

    function updateMessage(
        id: string,
        updates: Partial<Message>
    ) {
        setMessages(prev =>
            prev.map(message =>
                message.id === id
                    ? { ...message, ...updates }
                    : message
            )
        );
    }

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


            const assistantId = crypto.randomUUID();

            const assistantMessage: Message = {
                id: assistantId,
                role: "assistant",
                content: "",
                createdAt: new Date(),
            };
            setMessages(prev => [
                ...prev,
                assistantMessage,
            ]);

            const response: ChatResponse = await sendMessageToAI(text);

            updateMessage(assistantId, {
                content: response.content,
                sources: response.sources,
            });
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


