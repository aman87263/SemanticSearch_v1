import { useEffect, useMemo, useSyncExternalStore } from "react";

import { hasAuthToken, restoreSession } from "../auth/session";
import { AuthContext } from "./AuthContextValue";

const JUST_LOGGED_IN_KEY = "semanticsearch_just_logged_in";

function subscribeAuthChanges(onStoreChange: () => void) {
    window.addEventListener("auth-changed", onStoreChange);
    window.addEventListener("storage", onStoreChange);

    return () => {
        window.removeEventListener("auth-changed", onStoreChange);
        window.removeEventListener("storage", onStoreChange);
    };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const isAuthenticated = useSyncExternalStore(
        subscribeAuthChanges,
        () => hasAuthToken(),
        () => false,
    );

    // Restore session from cookie on app initialization
    // Skip on login pages and immediately after login to avoid race with session creation
    useEffect(() => {
        // Don't run on login/callback page - session is being created there
        if (window.location.pathname.startsWith("/login")) {
            return;
        }

        // Skip if we just logged in - the LoginCallbackPage already set the access token
        if (sessionStorage.getItem(JUST_LOGGED_IN_KEY) === "true") {
            sessionStorage.removeItem(JUST_LOGGED_IN_KEY);
            return;
        }

        let mounted = true;
        let restoreAttempted = false;

        const attemptRestore = async () => {
            if (restoreAttempted) return;
            restoreAttempted = true;

            try {
                const restored = await restoreSession();
                if (mounted && restored) {
                    // Session restored, auth state will update via notifyAuthChanged
                }
            } catch {
                // Ignore restore errors - user will need to login
            }
        };

        attemptRestore();

        return () => {
            mounted = false;
        };
    }, []);

    const value = useMemo(() => ({ isAuthenticated }), [isAuthenticated]);

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}


