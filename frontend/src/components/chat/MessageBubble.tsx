import { Box, Typography } from "@mui/material";
import type { Message } from "../../types/chat";

interface MessageBubbleProps {
    message: Message;
}

export default function MessageBubble({
    message,
}: MessageBubbleProps) {
    const isUser = message.role === "user";

    return (
        <Box
            sx={{
                display: "flex",
                justifyContent: isUser ? "flex-end" : "flex-start",
            }}
        >
            <Box
                sx={{
                    maxWidth: "75%",
                    px: 2,
                    py: 1.5,
                    borderRadius: 2,
                    bgcolor: isUser ? "#1976d2" : "#f5f5f5",
                    color: isUser ? "white" : "black",
                    whiteSpace: "pre-wrap",
                    lineHeight: 1.6,
                }}
            >
                <Typography variant="body2">
                    {message.content}
                </Typography>
            </Box>
        </Box>
    );
}