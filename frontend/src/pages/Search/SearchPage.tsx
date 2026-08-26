import { useState, type FormEvent } from "react";
import {
    Alert,
    Box,
    Button,
    Card,
    CardContent,
    CircularProgress,
    Stack,
    TextField,
    Typography,
} from "@mui/material";

import { searchDocuments } from "../../services/searchService";
import type { SearchResult } from "../../types/search";


export default function SearchPage() {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<SearchResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();

        const trimmedQuery = query.trim();
        if (!trimmedQuery) {
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await searchDocuments(trimmedQuery);
            setResults(response.results);
        } catch (requestError) {
            setError(
                requestError instanceof Error
                    ? requestError.message
                    : "Search failed. Please try again.",
            );
        } finally {
            setLoading(false);
        }
    }

    return (
        <Box sx={{ p: 3, maxWidth: 1000, width: "100%", mx: "auto" }}>
            <Typography variant="h4" gutterBottom>
                Search documents
            </Typography>

            <Box component="form" onSubmit={handleSubmit} sx={{ display: "flex", gap: 1, mb: 3 }}>
                <TextField
                    fullWidth
                    label="Search your documents"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    disabled={loading}
                />
                <Button type="submit" variant="contained" disabled={loading}>
                    Search
                </Button>
            </Box>

            {loading && <CircularProgress size={28} />}
            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

            {!loading && !error && query && results.length === 0 && (
                <Typography color="text.secondary">No matching chunks found.</Typography>
            )}

            <Stack spacing={2}>
                {results.map((result) => (
                    <Card key={result.id} variant="outlined">
                        <CardContent>
                            <Typography variant="subtitle1">
                                {result.document_name ?? "Unknown document"}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                                Chunk {result.index + 1} · similarity {result.similarity.toFixed(3)}
                            </Typography>
                            <Typography sx={{ mt: 1, whiteSpace: "pre-wrap" }}>
                                {result.text}
                            </Typography>
                        </CardContent>
                    </Card>
                ))}
            </Stack>
        </Box>
    );
}
