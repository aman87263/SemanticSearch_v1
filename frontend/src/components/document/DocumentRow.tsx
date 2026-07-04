import {
    IconButton,
    TableCell,
    TableRow,
} from "@mui/material";

import DeleteIcon from "@mui/icons-material/Delete";

import type { Document } from "../../types/document";
import { useDocuments } from "../../hooks/useDocuments";

interface DocumentRowProps {
    document: Document;
}

export default function DocumentRow({
    document,
}: DocumentRowProps) {

    const { deleteDocument } = useDocuments();

    return (
        <TableRow hover>
            <TableCell>
                {document.name}
            </TableCell>

            <TableCell>
                {document.status}
            </TableCell>

            <TableCell align="right">
                {(document.size / 1024).toFixed(1)} KB
            </TableCell>

            <TableCell align="right">
                {document.chunkCount ?? "-"}
            </TableCell>

            <TableCell>
                {document.uploadedAt.toLocaleTimeString()}
            </TableCell>

            <TableCell align="center">
                <IconButton
                    color="error"
                    onClick={() => deleteDocument(document.id)}
                >
                    <DeleteIcon />
                </IconButton>
            </TableCell>
        </TableRow>
    );
}