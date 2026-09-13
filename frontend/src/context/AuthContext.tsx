import { createContext, useContext, useMemo, useSyncExternalStore } from "react";

import { hasAuthToken } from "../auth/session";

interface AuthContextValue {
    isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

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

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) {
        throw new Error("useAuth must be used inside AuthProvider");
    }

    return ctx;
}
