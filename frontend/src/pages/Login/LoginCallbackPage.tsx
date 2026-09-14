import { useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Box, Typography, CircularProgress } from "@mui/material";

import {
    clearOAuthState,
    isOAuthStateValid,
    notifyAuthChanged,
    setAccessToken,
} from "../../auth/session";
import { keycloakConfig } from "../../config/keycloak";

const API_BASE_URL =
    (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
    "http://localhost:8000/api";

/** Survives React Strict Mode remounts so we do not validate/consume state twice. */
let inflightAuthCode: string | null = null;

export default function LoginCallbackPage() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const didExchange = useRef(false);

    useEffect(() => {
        const code = searchParams.get("code");
        const state = searchParams.get("state");

        if (!code) {
            return;
        }

        if (inflightAuthCode === code || didExchange.current) {
            return;
        }

        if (!isOAuthStateValid(state)) {
            navigate("/login", { replace: true, state: { error: "Login session state did not match. Please try signing in again." } });
            return;
        }

        didExchange.current = true;
        inflightAuthCode = code;

        const authCode = code;

        async function exchangeCode() {
            try {
                // Exchange authorization code with backend (BFF pattern)
                // Backend will exchange code with Keycloak, store refresh token server-side,
                // set HttpOnly session cookie, and return access token for in-memory storage
                const sessionResponse = await fetch(
                    `${API_BASE_URL}/auth/session`,
                    {
                        method: "POST",
                        credentials: "include",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({
                            code: authCode,
                            code_verifier: "", // PKCE not yet implemented on frontend
                            redirect_uri: keycloakConfig.redirectUri,
                        }),
                    }
                );

                if (!sessionResponse.ok) {
                    const errorText = await sessionResponse.text();
                    throw new Error(
                        `Session creation failed (${sessionResponse.status}): ${errorText}`
                    );
                }

                const sessionPayload = await sessionResponse.json() as {
                    success?: boolean;
                    data?: {
                        authenticated?: boolean;
                        user_id?: string;
                        roles?: string[];
                        provider?: string;
                        access_token?: string;
                        expires_in?: number;
                        session_id?: string;
                    };
                };

                if (!sessionPayload.success || !sessionPayload.data?.authenticated) {
                    throw new Error("Backend session creation did not return an authenticated session.");
                }

                // Store access token in memory only (never in localStorage/sessionStorage)
                const accessToken = sessionPayload.data.access_token ?? null;
                setAccessToken(accessToken);

                // Notify auth state change
                clearOAuthState();
                notifyAuthChanged();

                navigate("/chat", { replace: true });
            } catch (caughtError) {
                inflightAuthCode = null;
                didExchange.current = false;
                navigate("/login", {
                    replace: true,
                    state: {
                        error: caughtError instanceof Error
                            ? caughtError.message
                            : "Unable to complete the Keycloak login.",
                    },
                });
            }
        }

        void exchangeCode();
    }, [navigate, searchParams]);

    return (
        <Box sx={{ p: 4, display: "flex", flexDirection: "column", minHeight: "50vh", alignItems: "center", justifyContent: "center", gap: 2 }}>
            <CircularProgress />
            <Typography variant="h6">Completing Keycloak login…</Typography>
        </Box>
    );
}
