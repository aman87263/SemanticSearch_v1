import { Box, Button, Typography, Paper, Alert } from "@mui/material";
import { Navigate, useLocation } from "react-router-dom";

import { redirectToKeycloakLogin } from "../../config/keycloak";
import { useAuth } from "../../context/useAuth";

export default function LoginPage() {
    const { isAuthenticated } = useAuth();
    const location = useLocation();
    const redirectTo =
        (location.state as { from?: string } | null)?.from ?? "/documents";
    const routeError =
        (location.state as { error?: string } | null)?.error ?? null;

    if (isAuthenticated) {
        return <Navigate to={redirectTo} replace />;
    }

    return (
        <Box sx={{ p: 4, display: "flex", alignItems: "center", justifyContent: "center", minHeight: "60vh" }}>
            <Paper sx={{ p: 4, maxWidth: 560, width: "100%" }}>
                <Typography variant="h4" sx={{ mb: 2 }}>Sign in</Typography>
                <Typography variant="body1" sx={{ mb: 3 }}>
                    Continue with the local Keycloak identity provider.
                </Typography>
                {routeError && (
                    <Alert severity="error" sx={{ mb: 2 }}>{routeError}</Alert>
                )}
                <Button
                    variant="contained"
                    size="large"
                    fullWidth
                    onClick={redirectToKeycloakLogin}
                >
                    Login
                </Button>
            </Paper>
        </Box>
    );
}