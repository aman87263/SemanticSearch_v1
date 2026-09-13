import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Box, Typography, CircularProgress, Alert } from "@mui/material";

import {
    clearOAuthState,
    isOAuthStateValid,
    notifyAuthChanged,
    persistAuthSession,
} from "../../auth/session";
import { keycloakConfig } from "../../config/keycloak";

/** Survives React Strict Mode remounts so we do not validate/consume state twice. */
let inflightAuthCode: string | null = null;

function decodeJwtPayload(token: string): Record<string, unknown> | null {
    try {
        const payload = token.split(".")[1];
        if (!payload) {
            return null;
        }

        const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
        const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), "=");
        return JSON.parse(atob(padded));
    } catch {
        return null;
    }
}

export default function LoginCallbackPage() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [error, setError] = useState<string | null>(null);
    const didExchange = useRef(false);

    useEffect(() => {
        const code = searchParams.get("code");
        const state = searchParams.get("state");

        if (!code) {
            setError("Keycloak callback did not include the expected authorization code.");
            return;
        }

        if (inflightAuthCode === code || didExchange.current) {
            return;
        }

        if (!isOAuthStateValid(state)) {
            setError("Login session state did not match. Please try signing in again.");
            return;
        }

        didExchange.current = true;
        inflightAuthCode = code;

        const authCode = code;

        async function exchangeCode() {
            try {
                const body = new URLSearchParams({
                    grant_type: "authorization_code",
                    client_id: keycloakConfig.clientId,
                    code: authCode,
                    redirect_uri: keycloakConfig.redirectUri,
                });

                const response = await fetch(
                    `${keycloakConfig.url}/realms/${keycloakConfig.realm}/protocol/openid-connect/token`,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/x-www-form-urlencoded",
                        },
                        body: body.toString(),
                    }
                );

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`Token exchange failed (${response.status}): ${errorText}`);
                }

                const tokenSet = await response.json() as {
                    access_token?: string;
                    refresh_token?: string;
                    id_token?: string;
                };

                if (!tokenSet.access_token) {
                    throw new Error("Access token was not returned by Keycloak.");
                }

                const payload = decodeJwtPayload(tokenSet.access_token) ?? {};
                const roles =
                    (payload?.realm_access as { roles?: string[] } | undefined)?.roles ??
                    ["USER"];
                const userId =
                    (payload?.sub as string | undefined) ||
                    (payload?.preferred_username as string | undefined) ||
                    "keycloak-user";

                persistAuthSession({
                    accessToken: tokenSet.access_token,
                    refreshToken: tokenSet.refresh_token,
                    idToken: tokenSet.id_token,
                    userId,
                    roles,
                    provider: "keycloak",
                });

                clearOAuthState();
                notifyAuthChanged();

                navigate("/documents", { replace: true });
            } catch (caughtError) {
                inflightAuthCode = null;
                didExchange.current = false;
                setError(caughtError instanceof Error ? caughtError.message : "Unable to complete the Keycloak login.");
            }
        }

        void exchangeCode();
    }, [navigate, searchParams]);

    return (
        <Box sx={{ p: 4, display: "flex", flexDirection: "column", minHeight: "50vh", alignItems: "center", justifyContent: "center", gap: 2 }}>
            {error ? (
                <Alert severity="error">{error}</Alert>
            ) : (
                <>
                    <CircularProgress />
                    <Typography variant="h6">Completing Keycloak login…</Typography>
                </>
            )}
        </Box>
    );
}
