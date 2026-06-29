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

import { NavLink } from "react-router-dom";

export default function Sidebar() {

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

            <Box p={2}>
                <Typography variant="h6">
                    AI Knowledge Assistant
                </Typography>
            </Box>

            <Box px={2}>
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

                <ListItemButton component={NavLink} to="/chat">

                    <ListItemIcon>
                        <ChatIcon />
                    </ListItemIcon>

                    <ListItemText primary="Chat" />

                </ListItemButton>

                <ListItemButton component={NavLink} to="/documents">

                    <ListItemIcon>
                        <DescriptionIcon />
                    </ListItemIcon>

                    <ListItemText primary="Documents" />

                </ListItemButton>

                <ListItemButton component={NavLink} to="/settings">

                    <ListItemIcon>
                        <SettingsIcon />
                    </ListItemIcon>

                    <ListItemText primary="Settings" />

                </ListItemButton>

            </List>

        </Box>
    );

}