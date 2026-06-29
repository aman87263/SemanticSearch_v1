import { useEffect, useRef, useState } from "react";
import { Box } from "@mui/material";
import ChatInput from "../../components/chat/ChatInput";
import MessageList from "../../components/chat/MessageList";
import type { Message } from "../../types/chat";

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: crypto.randomUUID(),
            role: "assistant",
            content: "Hi! Ask me anything from your documents.",
            createdAt: new Date(),
        },
    ]);

    const endRef = useRef<HTMLDivElement | null>(null);

    const scrollToBottom = () => {
        endRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = (text: string) => {
        const userMessage: Message = {
            id: crypto.randomUUID(),
            role: "user",
            content: text,
            createdAt: new Date(),
        };

        const fullResponse =
            "This is a streamed response. Later this will come from your RAG backend with real token streaming.";

        // add user message + empty assistant message
        setMessages((prev) => [
            ...prev,
            userMessage,
            { role: "assistant", content: "", id: crypto.randomUUID(), createdAt: new Date() },
        ]);

        let index = 0;

        const interval = setInterval(() => {
            index++;

            setMessages((prev) => {
                const updated = [...prev];
                const lastMsg = updated[updated.length - 1];

                if (lastMsg.role === "assistant") {
                    lastMsg.content = fullResponse.slice(0, index);
                }

                return updated;
            });

            if (index >= fullResponse.length) {
                clearInterval(interval);
            }
        }, 20); // speed of streaming
    };

    return (
        <Box
            sx={{
                display: "flex",
                flexDirection: "column",
                height: "100%",
                alignItems: "center",
            }}
        >
            {/* Centered chat container like ChatGPT */}
            <Box
                sx={{
                    width: "100%",
                    maxWidth: "800px",
                    flex: 1,
                    display: "flex",
                    flexDirection: "column",
                }}
            >
                <MessageList messages={messages} />

                <div ref={endRef} />
                <ChatInput onSend={handleSend} />
            </Box>
        </Box>
    );
}