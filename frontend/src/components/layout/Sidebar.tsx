import {
    Box,
    Button,
    Divider,
    List,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Typography
} from "@mui/material";

import ChatIcon from "@mui/icons-material/Chat";
import DescriptionIcon from "@mui/icons-material/Description";
import SettingsIcon from "@mui/icons-material/Settings";
import AddIcon from "@mui/icons-material/Add";
import SearchIcon from "@mui/icons-material/Search";
import LoginIcon from "@mui/icons-material/Login";
import LogoutIcon from "@mui/icons-material/Logout";

import { NavLink } from "react-router-dom";
import { clearAuthSession, notifyAuthChanged } from "../../auth/session";
import { getKeycloakLogoutUrl, redirectToKeycloakLogin } from "../../config/keycloak";
import { useAuth } from "../../context/useAuth";

const API_BASE_URL =
    (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
    "http://localhost:8000/api";

export default function Sidebar() {
    const { isAuthenticated } = useAuth();

    const handleLogout = async () => {
        // First, call backend to invalidate server-side session and clear HttpOnly cookie
        try {
            await fetch(`${API_BASE_URL}/auth/logout`, {
                method: "POST",
                credentials: "include",
            });
        } catch {
            // Ignore errors - we still want to clear local state and redirect to Keycloak
        }

        // Clear local in-memory auth state
        clearAuthSession();
        notifyAuthChanged();

        // Redirect to Keycloak logout (no id_token_hint since we don't store id_token)
        window.location.assign(getKeycloakLogoutUrl(null));
    };

    const menuItems = [
        { label: "Chat", icon: <ChatIcon />, path: "/chat" },
        { label: "Documents", icon: <DescriptionIcon />, path: "/documents" },
        { label: "Search", icon: <SearchIcon />, path: "/search" },
        { label: "Settings", icon: <SettingsIcon />, path: "/settings" },
    ];
    return (
        <Box
            sx={{
                width: 280,
                height: "100%",
                display: "flex",
                flexDirection: "column",
                borderRight: "1px solid #e0e0e0",
            }}
        >

            <Box sx={{ p: 2 }}>
                <Typography variant="h6">
                    AI Knowledge Assistant
                </Typography>
            </Box>

            <Box sx={{ px: 2 }}>
                <Button
                    fullWidth
                    startIcon={<AddIcon />}
                    variant="contained"
                >
                    New Chat
                </Button>
            </Box>

            <Divider sx={{ my: 2 }} />

            <List>

                {menuItems.map((item) => (
                    <ListItemButton key={item.path} component={NavLink} to={item.path}>
                        <ListItemIcon>
                            {item.icon}
                        </ListItemIcon>

                        <ListItemText primary={item.label} />

                    </ListItemButton>
                ))}

                {!isAuthenticated && (
                    <ListItemButton
                        component="button"
                        onClick={redirectToKeycloakLogin}
                    >
                        <ListItemIcon>
                            <LoginIcon />
                        </ListItemIcon>
                        <ListItemText primary="Login" />
                    </ListItemButton>
                )}

                {isAuthenticated && (
                    <ListItemButton
                        component="button"
                        onClick={handleLogout}
                    >
                        <ListItemIcon>
                            <LogoutIcon />
                        </ListItemIcon>
                        <ListItemText primary="Logout" />
                    </ListItemButton>
                )}

            </List>

        </Box>
    );

}
