import { apiClient, ApiError } from './apiClient';
import { 
  LoginRequest, 
  LoginResponse, 
  RefreshResponse, 
  LogoutResponse, 
  AuthUserInfo,
  SignupRequest,
  UserResponse,
  MessageResponse,
  ChangePasswordRequest
} from '../types';

export { ApiError as AuthError } from './apiClient';

export const authService = {
  getAccessToken(): string | null {
    return apiClient.token.get();
  },

  setAccessToken(token: string | null): void {
    apiClient.token.set(token);
  },

  isAuthenticated(): boolean {
    return Boolean(apiClient.token.get());
  },

  /**
   * Public user signup endpoint:
   * POST /api/v1/auth/signup
   */
  async signup(payload: SignupRequest): Promise<UserResponse> {
    return apiClient.post<UserResponse>('/auth/signup', {
      name: payload.name.trim(),
      email: payload.email.trim().toLowerCase(),
      password: payload.password,
    }, { skipAuth: true });
  },

  /**
   * Authenticate user credentials:
   * POST /api/v1/auth/login
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const data = await apiClient.post<LoginResponse>('/auth/login', {
      email: credentials.email.trim().toLowerCase(),
      password: credentials.password,
    }, { skipAuth: true });

    if (data?.access_token) {
      apiClient.token.set(data.access_token);
    }
    return data;
  },

  /**
   * Refresh short-lived access token:
   * POST /api/v1/auth/refresh
   */
  async refresh(): Promise<RefreshResponse> {
    const data = await apiClient.post<RefreshResponse>('/auth/refresh', {}, { skipAuth: true });
    if (data?.access_token) {
      apiClient.token.set(data.access_token);
    }
    return data;
  },

  /**
   * Revoke current session:
   * POST /api/v1/auth/logout
   */
  async logout(): Promise<LogoutResponse> {
    try {
      const res = await apiClient.post<MessageResponse>('/auth/logout');
      return { success: true, message: res.message };
    } catch {
      return { success: false };
    } finally {
      apiClient.token.clear();
    }
  },

  /**
   * Fetch currently authenticated user:
   * GET /api/v1/auth/me
   */
  async getMe(): Promise<AuthUserInfo | null> {
    try {
      return await apiClient.get<AuthUserInfo>('/auth/me');
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 401) {
        apiClient.token.clear();
      }
      return null;
    }
  },

  /**
   * Change current authenticated user's password:
   * POST /api/v1/auth/change-password
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<MessageResponse> {
    const payload: ChangePasswordRequest = {
      current_password: currentPassword,
      new_password: newPassword,
    };
    const res = await apiClient.post<MessageResponse>('/auth/change-password', payload);
    apiClient.token.clear();
    return res;
  },
};
