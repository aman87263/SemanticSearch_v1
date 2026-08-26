import { createContext } from "react";

import type { Message } from "../types/chat";

export interface ChatContextType {
    messages: Message[];
    loading: boolean;
    sendMessage: (text: string) => Promise<void>;
}

export const ChatContext = createContext<ChatContextType | undefined>(undefined);
