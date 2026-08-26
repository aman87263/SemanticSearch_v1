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

import { NavLink } from "react-router-dom";

export default function Sidebar() {
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


            </List>

        </Box>
    );

}
