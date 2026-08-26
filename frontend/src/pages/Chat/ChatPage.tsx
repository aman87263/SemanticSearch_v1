import { Box } from "@mui/material";
import ChatInput from "../../components/chat/ChatInput";
import MessageList from "../../components/chat/MessageList";
import { useChat } from "../../hooks/useChat";

export default function ChatPage() {
    const { messages, sendMessage, loading } = useChat();

    return (
        <Box
            sx={{
                display: "flex",
                flexDirection: "column",
                height: "100%",
                alignItems: "center",
            }}
        >
            <Box
                sx={{
                    width: "100%",
                    maxWidth: "900px",
                    flex: 1,
                    display: "flex",
                    flexDirection: "column",
                }}
            >
                <MessageList messages={messages} />

                {loading && (
                    <Box sx={{ px: 2, py: 1 }}>
                        AI is thinking...
                    </Box>
                )}

                <ChatInput onSend={sendMessage} disabled={loading} />
            </Box>
        </Box>
    );
}
