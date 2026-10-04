import { useEffect, useMemo, useState, useSyncExternalStore } from "react";

import { hasAuthToken, restoreSession } from "../auth/session";
import { AuthContext } from "./AuthContextValue";

function subscribeAuthChanges(onStoreChange: () => void) {
    window.addEventListener("auth-changed", onStoreChange);
    window.addEventListener("storage", onStoreChange);

    return () => {
        window.removeEventListener("auth-changed", onStoreChange);
        window.removeEventListener("storage", onStoreChange);
    };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [isInitializing, setIsInitializing] = useState(
        () => !window.location.pathname.startsWith("/login"),
    );
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

        let mounted = true;
        void restoreSession().finally(() => {
            if (mounted) {
                setIsInitializing(false);
            }
        });

        return () => {
            mounted = false;
        };
    }, []);

    const value = useMemo(
        () => ({ isAuthenticated, isInitializing }),
        [isAuthenticated, isInitializing],
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}


