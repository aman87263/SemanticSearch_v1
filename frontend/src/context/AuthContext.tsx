import { useMemo, useSyncExternalStore } from "react";

import { hasAuthToken } from "../auth/session";
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
    const isAuthenticated = useSyncExternalStore(
        subscribeAuthChanges,
        () => hasAuthToken(),
        () => false,
    );

    const value = useMemo(() => ({ isAuthenticated }), [isAuthenticated]);

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}


