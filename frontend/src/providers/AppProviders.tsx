import { ChatProvider } from "../context/ChatContext";
import { DocumentProvider } from "../context/DocumentContext";


export function AppProviders({ children }: { children: React.ReactNode }) {
    return (
        <ChatProvider>
            <DocumentProvider>
                {children}
            </DocumentProvider>
        </ChatProvider>
    );
}