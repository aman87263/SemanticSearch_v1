import { useRef, useState } from "react";

import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import {
    Button,
    Paper,
    Typography
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
    const { uploadDocument } = useDocuments();
    const [isDragging, setIsDragging] = useState(false);

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

        if (!isSupportedFile(file)) {
            alert(`Only ${EXTENSION_LABELS} files are supported.`);
            return;
        }

        await uploadDocument(file);
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
                cursor: "pointer",
                "&:hover": {
                    borderColor: "primary.main",
                },
            }}
            onClick={() => fileInputRef.current?.click()}
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
        </Paper>
    );
}
