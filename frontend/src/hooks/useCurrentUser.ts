import { useEffect, useState } from "react";
import { useAuth } from "../context/useAuth";
import { apiRequest } from "../services/http/httpClient";

interface UserInfo {
    user_id: string;
    roles: string[];
    authenticated: boolean;
    provider: string;
    preferred_username: string;
    email?: string;
    name?: string;
}

export function useCurrentUser(): UserInfo | null {
    const { isAuthenticated } = useAuth();
    const [userInfo, setUserInfo] = useState<UserInfo | null>(null);

    useEffect(() => {
        if (!isAuthenticated) {
            return;
        }

        let mounted = true;

        apiRequest<{ success: boolean; data: UserInfo }>("/auth/me")
            .then(response => {
                if (mounted && response.success && response.data) {
                    setUserInfo(response.data);
                }
            })
            .catch(() => {
                if (mounted) {
                    setUserInfo(null);
                }
            });

        return () => {
            mounted = false;
        };
    }, [isAuthenticated]);

    // Clear user info when logged out
    useEffect(() => {
        if (!isAuthenticated) {
            // eslint-disable-next-line react-hooks/set-state-in-effect
            setUserInfo(null);
        }
    }, [isAuthenticated]);

    return userInfo;
}