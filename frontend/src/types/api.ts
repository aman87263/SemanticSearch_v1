export interface ApiError {
    code: string;
    message: string;
}

export interface ApiResponse<T> {
    success: boolean;
    status_code: number;
    data: T;
    error: ApiError | null;
}