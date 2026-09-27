import {
    Box,
    Button,
    Divider,
    List,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Typography,
    Avatar,
    Tooltip
} from "@mui/material";

import ChatIcon from "@mui/icons-material/Chat";
import DescriptionIcon from "@mui/icons-material/Description";
import SettingsIcon from "@mui/icons-material/Settings";
import AddIcon from "@mui/icons-material/Add";
import SearchIcon from "@mui/icons-material/Search";
import LoginIcon from "@mui/icons-material/Login";
import LogoutIcon from "@mui/icons-material/Logout";
import PersonIcon from "@mui/icons-material/Person";

import { NavLink } from "react-router-dom";
import React from "react";
import { clearAuthSession, notifyAuthChanged } from "../../auth/session";
import { getKeycloakLogoutUrl, redirectToKeycloakLogin } from "../../config/keycloak";
import { useAuth } from "../../context/useAuth";
import { apiRequest } from "../../services/http/httpClient";

interface UserInfo {
    user_id: string;
    roles: string[];
    authenticated: boolean;
    provider: string;
    preferred_username: string;
    email?: string;
    name?: string;
}

export default function Sidebar() {
    const { isAuthenticated } = useAuth();
    const [userInfo, setUserInfo] = React.useState<UserInfo | null>(null);

    // Fetch user info on authentication
    React.useEffect(() => {
        if (!isAuthenticated) {
            return;
        }

        let mounted = true;

        apiRequest<{ success: boolean; data: UserInfo }>("/auth/me")
            .then(response => {
                if (mounted && response.success && response.data) {
                    setUserInfo(response.data);
                }
            })
            .catch(() => {
                if (mounted) {
                    setUserInfo(null);
                }
            });

        return () => {
            mounted = false;
        };
    }, [isAuthenticated]);

    // Clear user info when logged out
    React.useEffect(() => {
        if (!isAuthenticated) {
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setUserInfo(null);
        }
    }, [isAuthenticated]);

    const handleLogout = async () => {
        // First, call backend to invalidate server-side session and clear HttpOnly cookie
        try {
            await fetch("/api/auth/logout", {
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

                {isAuthenticated && userInfo && (
                    <Box sx={{ px: 2, py: 1 }}>
                        <Tooltip title={userInfo.roles.includes("ADMIN") ? "Administrator" : "User"}>
                            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                                <Avatar variant="rounded" sx={{ width: 32, height: 32 }}>
                                    <PersonIcon fontSize="small" />
                                </Avatar>
                                <Box>
                                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                        {userInfo.preferred_username || userInfo.name || userInfo.email || "Unknown User"  }
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        {userInfo.roles.includes("ADMIN") ? "Administrator" : "User"}
                                    </Typography>
                                </Box>
                            </Box>
                        </Tooltip>
                    </Box>
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
