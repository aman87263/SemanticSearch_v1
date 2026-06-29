import { Box } from "@mui/material";
import type { Message } from "../../types/chat";
import MessageBubble from "./MessageBubble";

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
            {messages.map((message, index) => (
                <MessageBubble
                    key={index}
                    message={message}
                />
            ))}
        </Box>
    );
}