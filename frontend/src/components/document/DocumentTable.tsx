import {
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Typography,
} from "@mui/material";

import { useDocuments } from "../../hooks/useDocuments";
import DocumentRow from "./DocumentRow";


export default function DocumentTable() {
    const { documents } = useDocuments();

    if (documents.length === 0) {
        return (
            <Typography
                variant="body1"
                color="text.secondary"
                sx={{ mt: 4, textAlign: "center" }}
            >
                No documents uploaded yet.
            </Typography>
        );
    }

    return (
        <TableContainer component={Paper} sx={{ mt: 4 }}>
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell align="right">Size</TableCell>
                        <TableCell align="right">Chunks</TableCell>
                        <TableCell>Uploaded</TableCell>
                        <TableCell align="center">Actions</TableCell>
                    </TableRow>
                </TableHead>

                <TableBody>
                    {documents.map(document => (
                        <DocumentRow
                            key={document.id}
                            document={document}
                        />
                    ))}
                </TableBody>
            </Table>
        </TableContainer>
    );
}