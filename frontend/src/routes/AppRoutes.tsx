import { Routes, Route, Navigate } from "react-router-dom";

import ChatPage from "../pages/Chat/ChatPage";
import DocumentsPage from "../pages/Documents/DocumentsPage";
import SettingsPage from "../pages/Settings/SettingsPage";
import LoginPage from "../pages/Login/LoginPage";
import LoginCallbackPage from "../pages/Login/LoginCallbackPage";
import SearchPage from "../pages/Search/SearchPage";
import ProtectedRoute from "./ProtectedRoute";

function AdminUsersPlaceholder() {
    return (
        <div style={{ padding: 24 }}>
            <h1>Admin Users</h1>
            <p>This UI page is a placeholder until the admin users page is implemented.</p>
        </div>
    );
}

export default function AppRoutes() {
    return (
        <Routes>
            <Route
                path="/"
                element={
                        <Navigate to="/chat" replace />
                }
            />

            <Route
                path="/chat"
                element={
                        <ChatPage />
                }
            />
            <Route
                path="/documents"
                element={
                    <ProtectedRoute>
                        <DocumentsPage />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/search"
                element={
                    <ProtectedRoute>
                        <SearchPage />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/settings"
                element={
                    <ProtectedRoute>
                        <SettingsPage />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/admin/users"
                element={
                    <ProtectedRoute>
                        <AdminUsersPlaceholder />
                    </ProtectedRoute>
                }
            />

            <Route path="/login" element={<LoginPage />} />
            <Route path="/login/callback" element={<LoginCallbackPage />} />

            <Route path="*" element={<h1>404 - Page Not Found</h1>} />
        </Routes>
    );
}
