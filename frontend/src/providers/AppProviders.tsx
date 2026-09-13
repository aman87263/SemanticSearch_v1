import { AuthProvider } from "../context/AuthContext";
import { ChatProvider } from "../context/ChatContext";
import { DocumentProvider } from "../context/DocumentContext";


export function AppProviders({ children }: { children: React.ReactNode }) {
    return (
        <AuthProvider>
            <ChatProvider>
                <DocumentProvider>
                    {children}
                </DocumentProvider>
            </ChatProvider>
        </AuthProvider>
    );
}