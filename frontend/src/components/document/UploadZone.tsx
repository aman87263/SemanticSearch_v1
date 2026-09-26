import { useRef, useState } from "react";

import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import CircularProgress from "@mui/material/CircularProgress";
import {
    Box,
    Button,
    Paper,
    Typography,
    Alert
} from "@mui/material";

import { useDocuments } from "../../hooks/useDocuments";
import {
    EXTENSION_LABELS,
    SUPPORTED_EXTENSIONS,
} from "./uploadConstants";

function getFileExtension(fileName: string): string {
    const dotIndex = fileName.lastIndexOf(".");

    if (dotIndex === -1) {
        return "";
    }

    return fileName.slice(dotIndex).toLowerCase();
}

function isSupportedFile(file: File): boolean {
    return SUPPORTED_EXTENSIONS.includes(getFileExtension(file.name));
}

export default function UploadZone() {
    const { uploadDocument, loading } = useDocuments();
    const [isDragging, setIsDragging] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fileInputRef = useRef<HTMLInputElement>(null);

    function handleDragOver(
        event: React.DragEvent<HTMLDivElement>
    ) {
        event.preventDefault();

        setIsDragging(true);
    }

    function handleDragLeave() {
        setIsDragging(false);
    }

    async function handleDrop(
        event: React.DragEvent<HTMLDivElement>
    ) {
        event.preventDefault();

        setIsDragging(false);

        const file = event.dataTransfer.files[0];
        await uploadSelectedFile(file);
    }

    async function uploadSelectedFile(file?: File) {
        if (!file) {
            return;
        }

        setError(null);

        if (!isSupportedFile(file)) {
            setError(`Only ${EXTENSION_LABELS} files are supported.`);
            return;
        }

        try {
            await uploadDocument(file);
        } catch (err) {
            const message = err instanceof Error ? err.message : "Upload failed. Please try again.";
            setError(message);
        }
    }

    async function handleFileSelect(
        event: React.ChangeEvent<HTMLInputElement>
    ) {
        const file = event.target.files?.[0];

        await uploadSelectedFile(file);

        event.target.value = "";
    }

    return (
        <Paper
            elevation={2}
            sx={{
                p: 5,
                textAlign: "center",
                border: "2px dashed",
                borderColor: isDragging
                    ? "primary.main"
                    : "divider",
                backgroundColor: isDragging
                    ? "action.hover"
                    : "transparent",
                cursor: loading ? "wait" : "pointer",
                "&:hover": {
                    borderColor: "primary.main",
                },
            }}
            onClick={loading ? undefined : () => fileInputRef.current?.click()}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
        >
            <input
                ref={fileInputRef}
                type="file"
                accept={SUPPORTED_EXTENSIONS.join(",")}
                hidden
                onChange={handleFileSelect}
                disabled={loading}
            />

            {error && (
                <Alert severity="error" sx={{ mb: 2, textAlign: "left" }}>
                    {error}
                </Alert>
            )}

            {loading ? (
                <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}>
                    <CircularProgress size={64} color="primary" />
                    <Typography variant="h6">Uploading document...</Typography>
                    <Typography variant="body2" color="text.secondary">
                        Please wait while the document is being processed.
                    </Typography>
                </Box>
            ) : (
                <>
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
                        Click anywhere or drag and drop {EXTENSION_LABELS} files here.
                    </Typography>

                    <Button
                        variant="contained"
                        onClick={(event) => {
                            event.stopPropagation();
                            fileInputRef.current?.click();
                        }}
                    >
                        Choose File
                    </Button>
                </>
            )}
        </Paper>
    );
}
