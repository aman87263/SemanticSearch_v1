import { Routes, Route, Navigate } from "react-router-dom";

import ChatPage from "../pages/Chat/ChatPage";
import DocumentsPage from "../pages/Documents/DocumentsPage";
import SettingsPage from "../pages/Settings/SettingsPage";
import LoginPage from "../pages/Login/LoginPage";

export default function AppRoutes() {
    return (
        <Routes>
            <Route path="/" element={<Navigate to="/chat" replace />} />

            <Route path="/chat" element={<ChatPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/settings" element={<SettingsPage />} />

            <Route path="/login" element={<LoginPage />} />

            <Route path="*" element={<h1>404 - Page Not Found</h1>} />
        </Routes>
    );
}