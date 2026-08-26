import { useContext } from "react";
import { ChatContext } from "../context/ChatContextValue";

export function useChat() {
    const context = useContext(ChatContext);

    if (!context) {
        throw new Error(
            "useChat must be used inside ChatProvider"
        );
    }

    return context;
}