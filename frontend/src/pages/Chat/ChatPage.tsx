import { useState } from "react";
import { Box } from "@mui/material";
import ChatInput from "../../components/chat/ChatInput";
import MessageList from "../../components/chat/MessageList";
import type { Message } from "../../types/chat";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hi! Ask me anything from your documents 🚀",
    },
  ]);

  const handleSend = (text: string) => {
    const userMessage: Message = { role: "user", content: text };

    // fake assistant response for now
    const assistantMessage: Message = {
      role: "assistant",
      content: "This is a mock response (backend coming later).",
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
      }}
    >
      <MessageList messages={messages} />
      <ChatInput onSend={handleSend} />
    </Box>
  );
}