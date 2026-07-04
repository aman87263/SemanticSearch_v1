import { Box, Typography } from "@mui/material";

import UploadZone from "../../components/document/UploadZone";
import DocumentTable from "../../components/document/DocumentTable";

export default function DocumentsPage() {
    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
                Documents
            </Typography>

            <UploadZone />

            <Box sx={{ mt: 4 }}>
                <DocumentTable />
            </Box>
        </Box>
    );
}