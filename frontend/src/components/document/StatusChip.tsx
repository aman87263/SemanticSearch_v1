import Chip from "@mui/material/Chip";

import type { DocumentStatus } from "../../types/document";

interface StatusChipProps {
    status: DocumentStatus;
}

export default function StatusChip({
    status,
}: StatusChipProps) {
    switch (status) {
        case "uploading":
            return (
                <Chip
                    label="Uploading"
                    color="warning"
                    size="small"
                />
            );

        case "processing":
            return (
                <Chip
                    label="Processing"
                    color="info"
                    size="small"
                />
            );

        case "ready":
            return (
                <Chip
                    label="Ready"
                    color="success"
                    size="small"
                />
            );

        case "failed":
            return (
                <Chip
                    label="Failed"
                    color="error"
                    size="small"
                />
            );

        default:
            return (
                <Chip
                    label={status}
                    size="small"
                />
            );
    }
}