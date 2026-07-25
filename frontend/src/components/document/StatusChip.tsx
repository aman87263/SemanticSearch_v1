import Chip from "@mui/material/Chip";

import type { DocumentStatus } from "../../types/document";

interface StatusChipProps {
    status: DocumentStatus;
    progress?: number;
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
    completed: {
        label: "Completed",
        color: "success",
    },
    failed: {
        label: "Failed",
        color: "error",
    },
} as const;
export default function StatusChip({
    status,
    progress,
}: StatusChipProps) {
    const config = statusConfig[status];
    const label =
    status === "uploading"
        ? `Uploading (${progress}%)`
        : status.charAt(0).toUpperCase() + status.slice(1);

    return (
        <Chip
            label={label}
            color={config?.color}
            size="small"
        />
    );
}