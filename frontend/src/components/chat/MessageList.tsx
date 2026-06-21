import { Box, Typography } from "@mui/material";
import type { Message } from "../../types/chat";

export default function MessageList({ messages }: { messages: Message[] }) {
    return (
        <Box
            sx={{
                flex: 1,
                overflowY: "auto",
                py: 3,
                px: 2,
                display: "flex",
                flexDirection: "column",
                gap: 2,
            }}
        >
            {messages.map((msg, idx) => (
                <Box
                    key={idx}
                    sx={{
                        display: "flex",
                        justifyContent:
                            msg.role === "user" ? "flex-end" : "flex-start",
                    }}
                >
                    <Box
                        sx={{
                            maxWidth: "75%",
                            px: 2,
                            py: 1.5,
                            borderRadius: 2,
                            bgcolor: msg.role === "user" ? "#1976d2" : "#f6f6f6",
                            border: msg.role === "assistant" ? "1px solid #eee" : "none",
                            color: msg.role === "user" ? "white" : "black",
                            fontSize: "0.95rem",
                            lineHeight: 1.5,
                            whiteSpace: "pre-wrap",
                        }}
                    >
                        <Typography variant="body2">
                            {msg.content}
                            {msg.role === "assistant" && (
                                <span className="cursor">|</span>
                            )}
                        </Typography>
                    </Box>
                </Box>
            ))}
        </Box>
    );
}