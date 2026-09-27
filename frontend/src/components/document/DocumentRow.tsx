import {
    IconButton,
    TableCell,
    TableRow,
    Typography,
    Chip,
} from "@mui/material";

import DeleteIcon from "@mui/icons-material/Delete";
import PersonIcon from "@mui/icons-material/Person";
import PublicIcon from "@mui/icons-material/Public";
import LockIcon from "@mui/icons-material/Lock";

import type { Document } from "../../types/document";
import { useDocuments } from "../../hooks/useDocuments";
import { useCurrentUser } from "../../hooks/useCurrentUser";
import StatusChip from "./StatusChip";

interface DocumentRowProps {
    document: Document;
}

export default function DocumentRow({
    document,
}: DocumentRowProps) {

    const { deleteDocument, updateDocumentVisibility } = useDocuments();
    const currentUser = useCurrentUser();
    // console.log("DocumentRow document:", document);
    const uploaderName = document.uploaderName || "Unknown";
    const uploaderEmail = document.uploaderEmail  || "Unknown";

    const isOwner = currentUser?.user_id === document.owner_id;
    const isAdmin = currentUser?.roles?.includes("ADMIN") ?? false;
    const canDelete = isOwner || isAdmin;

    const canUpdateVisibility = isOwner || isAdmin;

    const handleVisibilityToggle = () => {
        if (!canUpdateVisibility) return;
        const newVisibility = document.visibility === "PUBLIC" ? "PRIVATE" : "PUBLIC";
        updateDocumentVisibility(document.id, newVisibility);
    };

    return (
        <TableRow hover>
            <TableCell>
                {document.name}
            </TableCell>

            <TableCell>
                <Chip
                    label={document.visibility === "PUBLIC" ? "Public" : "Private"}
                    icon={document.visibility === "PUBLIC" ? <PublicIcon fontSize="small" /> : <LockIcon fontSize="small" />}
                    size="small"
                    color={document.visibility === "PUBLIC" ? "success" : "default"}
                    variant="outlined"
                    onClick={handleVisibilityToggle}
                    sx={{ cursor: canUpdateVisibility ? "pointer" : "default" }}
                    disabled={!canUpdateVisibility}
                />
            </TableCell>

            <TableCell>
                <Typography variant="body2" display="flex" alignItems="center" gap={1}>
                    <PersonIcon fontSize="small" color="action" />
                    {uploaderName}
                </Typography>
            </TableCell>
            <TableCell>
                {uploaderEmail}
            </TableCell>

            <TableCell>
                <StatusChip status={document.status} progress={document.progress} />
            </TableCell>

            <TableCell align="right">
                {(document.size / 1024).toFixed(1)} KB
            </TableCell>

            <TableCell align="right">
                {document.chunkCount ?? "-"}
            </TableCell>

            <TableCell>
                {document.uploadedAt ? new Date(document.uploadedAt).toLocaleTimeString() : "Loading..."}
            </TableCell>

            <TableCell align="center">
                <IconButton
                    color="error"
                    onClick={() => deleteDocument(document.id)}
                    disabled={!canDelete}
                    aria-label={canDelete ? "Delete document" : "Only owner or admin can delete"}
                >
                    <DeleteIcon />
                </IconButton>
            </TableCell>
        </TableRow>
    );
}
