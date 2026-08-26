import { Box } from "@mui/material";
import type { Message } from "../../types/chat";
import MessageBubble from "./MessageBubble";
import { useAutoScroll } from "../../hooks/useAutoScroll";



export default function MessageList({ messages }: { messages: Message[] }) {
    const bottomRef = useAutoScroll(messages);
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
            {messages.map((message) => (
                <MessageBubble
                    key={message.id}
                    message={message}
                />
            ))}
            <div ref={bottomRef} />
        </Box>
    );
}
