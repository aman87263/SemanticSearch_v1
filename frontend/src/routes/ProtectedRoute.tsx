import { Navigate, useLocation } from "react-router-dom";
import { Box, CircularProgress } from "@mui/material";

import { useAuth } from "../hooks/useAuth";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const { isAuthenticated, isInitializing } = useAuth();
    const location = useLocation();
    if (isInitializing) {
        return (
            <Box role="status" sx={{ display: "flex", justifyContent: "center", p: 4 }}>
                <CircularProgress size={24} />
            </Box>
        );
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace state={{ from: location.pathname }} />;
    }

    return children;
}
