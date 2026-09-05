import { API_BASE_URL } from './api';
import { LoginRequest, LoginResponse, RefreshResponse, LogoutResponse, AuthUserInfo } from '../types';

export class AuthError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'AuthError';
  }
}

// In-memory access token storage (short-lived, not persisted to localStorage/sessionStorage)
let inMemoryAccessToken: string | null = null;

const getBaseUrl = (): string => {
  return (API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/+$/, '');
};

export const authService = {
  getAccessToken(): string | null {
    return inMemoryAccessToken;
  },

  setAccessToken(token: string | null): void {
    inMemoryAccessToken = token;
  },

  isAuthenticated(): boolean {
    return Boolean(inMemoryAccessToken);
  },

  /**
   * Authenticate user credentials against FastAPI endpoint:
   * POST /api/v1/auth/login
   *
   * Sends { email, password } as JSON.
   * Uses credentials: 'include' so backend can set the HttpOnly refresh token cookie.
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const url = `${getBaseUrl()}/auth/login`;

    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          email: credentials.email.trim(),
          password: credentials.password,
        }),
      });
    } catch (networkError) {
      throw new AuthError(
        0,
        'Unable to connect to the authentication server. Please check your network connection or verify that the server is running.',
        networkError
      );
    }

    if (!response.ok) {
      let errorMessage = 'Authentication failed.';
      let details: unknown = null;

      try {
        const errorData = await response.json();
        details = errorData;
        if (typeof errorData?.detail === 'string') {
          errorMessage = errorData.detail;
        } else if (typeof errorData?.message === 'string') {
          errorMessage = errorData.message;
        }
      } catch {
        // Fallback for non-JSON error bodies
      }

      // Map HTTP error codes to safe user-facing explanations
      if (response.status === 401) {
        throw new AuthError(401, 'Invalid email or password.', details);
      }

      if (response.status === 403) {
        throw new AuthError(403, errorMessage || 'Account is inactive or access is restricted.', details);
      }

      if (response.status >= 500) {
        throw new AuthError(response.status, 'Authentication service is temporarily unavailable. Please try again later.', details);
      }

      throw new AuthError(response.status, errorMessage, details);
    }

    const data: LoginResponse = await response.json();

    if (data.access_token) {
      inMemoryAccessToken = data.access_token;
    }

    return data;
  },

  /**
   * Refresh the short-lived access token:
   * POST /api/v1/auth/refresh
   *
   * Relies solely on the browser-managed HttpOnly refresh token cookie.
   */
  async refresh(): Promise<RefreshResponse> {
    const url = `${getBaseUrl()}/auth/refresh`;

    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
    } catch (networkError) {
      throw new AuthError(0, 'Unable to reach the authentication server for token refresh.', networkError);
    }

    if (!response.ok) {
      inMemoryAccessToken = null;
      throw new AuthError(response.status, 'Session expired or refresh token invalid.');
    }

    const data: RefreshResponse = await response.json();
    if (data.access_token) {
      inMemoryAccessToken = data.access_token;
    }
    return data;
  },

  /**
   * Terminate the authentication session:
   * POST /api/v1/auth/logout
   *
   * Instructs backend to invalidate session and clear the HttpOnly cookie.
   */
  async logout(): Promise<LogoutResponse> {
    const url = `${getBaseUrl()}/auth/logout`;

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      if (inMemoryAccessToken) {
        headers['Authorization'] = `Bearer ${inMemoryAccessToken}`;
      }

      const response = await fetch(url, {
        method: 'POST',
        headers,
        credentials: 'include',
      });

      if (response.ok) {
        try {
          return await response.json();
        } catch {
          return { success: true };
        }
      }
      return { success: false };
    } catch {
      return { success: false };
    } finally {
      inMemoryAccessToken = null;
    }
  },

  /**
   * Fetch currently authenticated user identity:
   * GET /api/v1/auth/me
   */
  async getMe(): Promise<AuthUserInfo | null> {
    if (!inMemoryAccessToken) {
      return null;
    }

    const url = `${getBaseUrl()}/auth/me`;
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${inMemoryAccessToken}`,
        },
        credentials: 'include',
      });

      if (!response.ok) {
        return null;
      }

      return await response.json();
    } catch {
      return null;
    }
  },

  /**
   * Change current user's password:
   * POST /api/v1/auth/change-password
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<LogoutResponse> {
    const url = `${getBaseUrl()}/auth/change-password`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(inMemoryAccessToken ? { 'Authorization': `Bearer ${inMemoryAccessToken}` } : {}),
      },
      credentials: 'include',
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });

    if (!response.ok) {
      let errDetail = 'Failed to change password.';
      try {
        const d = await response.json();
        if (d.detail) errDetail = d.detail;
      } catch {
        // ignore
      }
      throw new AuthError(response.status, errDetail);
    }

    inMemoryAccessToken = null;
    return await response.json();
  },
};


