import Chip from "@mui/material/Chip";

import type { DocumentStatus } from "../../types/document";

interface StatusChipProps {
    status: DocumentStatus;
}
const statusConfig = {
    uploading: {
        label: "Uploading",
        color: "warning",
    },
    processing: {
        label: "Processing",
        color: "info",
    },
    ready: {
        label: "Ready",
        color: "success",
    },
    failed: {
        label: "Failed",
        color: "error",
    },
} as const;
export default function StatusChip({
    status,
}: StatusChipProps) {
    const config = statusConfig[status];
    return (
        <Chip
            label={config.label}
            color={config.color}
            size="small"
        />
    );
}