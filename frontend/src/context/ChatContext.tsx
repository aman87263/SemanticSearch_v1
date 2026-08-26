import {
    createContext,
    useState,
    type ReactNode
} from "react";

import { sendMessage as sendMessageToAI } from "../services/chatService";
import type { Message } from "../types/chat";

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


            const response = await sendMessageToAI(text);

            setMessages(prev => [
                ...prev,
                {
                    id: crypto.randomUUID(),
                    role: "assistant",
                    content: response.answer,
                    citations: response.citations,
                    createdAt: new Date(),
                },
            ]);
        } catch (error) {
            const message = error instanceof Error
                ? error.message
                : "Unable to get an answer from the server.";

            setMessages(prev => [
                ...prev,
                {
                    id: crypto.randomUUID(),
                    role: "assistant",
                    content: `Unable to answer your question: ${message}`,
                    createdAt: new Date(),
                },
            ]);
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


