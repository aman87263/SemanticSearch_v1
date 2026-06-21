import { useEffect, useRef, useState } from "react";
import { Box } from "@mui/material";
import ChatInput from "../../components/chat/ChatInput";
import MessageList from "../../components/chat/MessageList";
import type { Message } from "../../types/chat";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hi 👋 Ask me anything from your documents.",
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
    const userMessage: Message = { role: "user", content: text };

    setMessages((prev) => [...prev, userMessage]);

    // simulate AI delay (ChatGPT feel)
    setTimeout(() => {
      const assistantMessage: Message = {
        role: "assistant",
        content:
          "This is a simulated response. Later this will come from your RAG backend.",
      };

      setMessages((prev) => [...prev, assistantMessage]);
    }, 800);
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