import { Box } from "@mui/material";
import type { Message } from "../../types/chat";

export default function MessageList({ messages }: { messages: Message[] }) {
  return (
    <Box
      sx={{
        flex: 1,
        overflowY: "auto",
        padding: 2,
        display: "flex",
        flexDirection: "column",
        gap: 1.5,
      }}
    >
      {messages.map((msg, idx) => (
        <Box
          key={idx}
          sx={{
            alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
            maxWidth: "70%",
            padding: 1.5,
            borderRadius: 2,
            bgcolor: msg.role === "user" ? "#1976d2" : "#eeeeee",
            color: msg.role === "user" ? "white" : "black",
          }}
        >
          {msg.content}
        </Box>
      ))}
    </Box>
  );
}