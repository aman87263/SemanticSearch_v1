import { Box } from "@mui/material";
import type { Message } from "../../types/chat";
import MarkdownRenderer from "../common/MarkdownRenderer";

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
            {isUser ? (
                <Box
                    sx={{
                        maxWidth: "70%",
                        bgcolor: "#1976d2",
                        color: "white",
                        px: 2,
                        py: 1.5,
                        borderRadius: 2,
                    }}
                >
                    {message.content}
                </Box>
            ) : (
                <Box
                    sx={{
                        width: "100%",
                        px: 2,
                        py: 1,
                    }}
                >
                    <MarkdownRenderer content={message.content} />
                </Box>
            )}
        </Box>
    );
}