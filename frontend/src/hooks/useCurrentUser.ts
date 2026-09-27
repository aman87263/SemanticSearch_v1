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
        if (isAuthenticated) {
            apiRequest<{ success: boolean; data: UserInfo }>("/auth/me")
                .then(response => {
                    if (response.success && response.data) {
                        setUserInfo(response.data);
                    }
                })
                .catch(() => setUserInfo(null));
        } else {
            setUserInfo(null);
        }
    }, [isAuthenticated]);

    return userInfo;
}