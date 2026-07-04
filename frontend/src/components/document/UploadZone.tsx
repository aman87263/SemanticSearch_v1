import { useRef } from "react";

import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import {
    Button,
    Paper,
    Typography
} from "@mui/material";

import { useDocuments } from "../../hooks/useDocuments";
export const SUPPORTED_FILE_TYPES = [
    "application/pdf",
];

export default function UploadZone() {
    const { uploadDocument } = useDocuments();

    const fileInputRef = useRef<HTMLInputElement>(null);

    async function handleFileSelect(
        event: React.ChangeEvent<HTMLInputElement>
    ) {
        const file = event.target.files?.[0];

        if (!file) {
            return;
        }

        if (!SUPPORTED_FILE_TYPES.includes(file.type)) {
            alert("Only PDF files are supported.");
            return;
        }

        await uploadDocument(file);

        // Allow selecting the same file again
        event.target.value = "";
    }

    return (
        <Paper
            elevation={2}
            sx={{
                p: 5,
                textAlign: "center",
                border: "2px dashed",
                borderColor: "divider",
                cursor: "pointer",
                "&:hover": {
                    borderColor: "primary.main",
                },
            }}
            onClick={() => fileInputRef.current?.click()}
        >
            <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                hidden
                onChange={handleFileSelect}
            />

            <CloudUploadIcon
                sx={{
                    fontSize: 64,
                    color: "primary.main",
                    mb: 2,
                }}
            />

            <Typography variant="h5" gutterBottom>
                Upload Documents
            </Typography>

            <Typography
                variant="body1"
                color="text.secondary"
                sx={{ mb: 3 }}
            >
                Click anywhere or drag & drop a PDF here.
            </Typography>

            <Button
                variant="contained"
                onClick={(e) => {
                    e.stopPropagation();
                    fileInputRef.current?.click();
                }}
            >
                Choose PDF
            </Button>
        </Paper>
    );
}