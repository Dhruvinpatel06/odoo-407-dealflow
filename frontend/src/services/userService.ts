import { API_BASE_URL } from './api';
import { authService, AuthError } from './authService';
import { AdminCreateUserRequest, UserResponse } from '../types';

const getBaseUrl = (): string => {
  return (API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/+$/, '');
};

export class UserAdminError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'UserAdminError';
  }
}

export const userService = {
  /**
   * Fetch all users from administrative endpoint:
   * GET /api/v1/users
   * Requires Admin Bearer token.
   */
  async getUsers(token?: string | null): Promise<UserResponse[]> {
    const activeToken = token || authService.getAccessToken();
    const url = `${getBaseUrl()}/users`;

    let response: Response;
    try {
      response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...(activeToken ? { Authorization: `Bearer ${activeToken}` } : {}),
        },
        credentials: 'include',
      });
    } catch (networkError) {
      throw new UserAdminError(0, 'Unable to connect to the backend server.', networkError);
    }

    if (!response.ok) {
      let errorMessage = 'Failed to fetch users.';
      try {
        const errorData = await response.json();
        if (typeof errorData?.detail === 'string') {
          errorMessage = errorData.detail;
        }
      } catch {
        // non-json
      }

      if (response.status === 401) {
        throw new UserAdminError(401, 'Authentication required to view users.');
      }
      if (response.status === 403) {
        throw new UserAdminError(403, 'Administrator permissions required to view users.');
      }
      throw new UserAdminError(response.status, errorMessage);
    }

    return await response.json();
  },

  /**
   * Admin create user endpoint:
   * POST /api/v1/users
   * Requires Admin Bearer token.
   * Sends name, email, password, role, is_active, and optional customer_id (omitted if empty).
   */
  async createUser(payload: AdminCreateUserRequest, token?: string | null): Promise<UserResponse> {
    const activeToken = token || authService.getAccessToken();
    const url = `${getBaseUrl()}/users`;

    const requestBody: Record<string, any> = {
      name: payload.name.trim(),
      email: payload.email.trim(),
      password: payload.password,
      role: payload.role,
      is_active: payload.is_active ?? true,
    };

    if (payload.customer_id && payload.customer_id.trim()) {
      requestBody.customer_id = payload.customer_id.trim();
    }

    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(activeToken ? { Authorization: `Bearer ${activeToken}` } : {}),
        },
        credentials: 'include',
        body: JSON.stringify(requestBody),
      });
    } catch (networkError) {
      throw new UserAdminError(
        0,
        'Unable to connect to the server. Please check your network connection or verify that the server is running.',
        networkError
      );
    }

    if (!response.ok) {
      let errorMessage = 'Failed to create user.';
      let details: unknown = null;

      try {
        const errorData = await response.json();
        details = errorData;
        if (typeof errorData?.detail === 'string') {
          errorMessage = errorData.detail;
        } else if (Array.isArray(errorData?.detail)) {
          errorMessage = errorData.detail.map((d: any) => d.msg || 'Validation error').join('; ');
        } else if (typeof errorData?.message === 'string') {
          errorMessage = errorData.message;
        }
      } catch {
        // non-json
      }

      if (response.status === 400) {
        throw new UserAdminError(400, errorMessage || 'Email already registered or invalid input.', details);
      }
      if (response.status === 401) {
        throw new UserAdminError(401, 'Authentication session expired or invalid. Please sign in again.', details);
      }
      if (response.status === 403) {
        throw new UserAdminError(403, 'Permission denied. Platform Administrator privileges required.', details);
      }
      if (response.status === 422) {
        throw new UserAdminError(422, errorMessage || 'Validation error. Please verify the form inputs.', details);
      }

      throw new UserAdminError(response.status, errorMessage, details);
    }

    return await response.json();
  },
};
