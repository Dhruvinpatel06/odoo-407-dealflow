import { apiClient, ApiError } from './apiClient';
import { 
  AdminCreateUserRequest, 
  UserResponse, 
  MessageResponse, 
  AdminChangePasswordRequest,
  UserRole
} from '../types';

export { ApiError as UserAdminError } from './apiClient';

export interface ListUsersParams {
  role?: UserRole | string;
  is_active?: boolean;
  skip?: number;
  limit?: number;
}

export const userService = {
  /**
   * List application users:
   * GET /api/v1/users
   * Accessible to ADMIN and SALES_MANAGER.
   */
  async getUsers(params?: ListUsersParams): Promise<UserResponse[]> {
    const query = new URLSearchParams();
    if (params?.role) query.append('role', params.role);
    if (params?.is_active !== undefined) query.append('is_active', String(params.is_active));
    if (params?.skip !== undefined) query.append('skip', String(params.skip));
    if (params?.limit !== undefined) query.append('limit', String(params.limit));

    const qs = query.toString();
    const endpoint = `/users${qs ? `?${qs}` : ''}`;
    return apiClient.get<UserResponse[]>(endpoint);
  },

  /**
   * Get single user details:
   * GET /api/v1/users/{id}
   * With fallback to user list if direct item route is unmapped.
   */
  async getUser(id: string): Promise<UserResponse> {
    try {
      return await apiClient.get<UserResponse>(`/users/${id}`);
    } catch (err: unknown) {
      if (err instanceof ApiError && (err.status === 404 || err.status === 405)) {
        const users = await this.getUsers();
        const found = users.find(u => u.id === id);
        if (found) return found;
      }
      throw err;
    }
  },

  /**
   * Update application user:
   * PATCH /api/v1/users/{id}
   */
  async updateUser(id: string, payload: Partial<UserResponse>): Promise<UserResponse> {
    return apiClient.patch<UserResponse>(`/users/${id}`, payload);
  },

  /**
   * List authorized deal approvers:
   * GET /api/v1/users/approvers
   * Fallback: filter list_users by SALES_MANAGER and FINANCE_OPERATIONS.
   */
  async getApprovers(): Promise<UserResponse[]> {
    try {
      return await apiClient.get<UserResponse[]>('/users/approvers');
    } catch (err: unknown) {
      if (err instanceof ApiError && (err.status === 404 || err.status === 405)) {
        const allUsers = await this.getUsers({ is_active: true });
        return allUsers.filter(
          u => u.role === 'SALES_MANAGER' || u.role === 'FINANCE_OPERATIONS' || u.role === 'ADMIN'
        );
      }
      throw err;
    }
  },

  /**
   * Admin create user endpoint:
   * POST /api/v1/users
   * Requires Admin authorization.
   */
  async createUser(payload: AdminCreateUserRequest): Promise<UserResponse> {
    const requestBody: Record<string, any> = {
      name: payload.name.trim(),
      email: payload.email.trim().toLowerCase(),
      password: payload.password,
      role: payload.role,
      is_active: payload.is_active ?? true,
    };

    if (payload.customer_id && payload.customer_id.trim()) {
      requestBody.customer_id = payload.customer_id.trim();
    }

    return apiClient.post<UserResponse>('/users', requestBody);
  },

  /**
   * Admin reset user password:
   * POST /api/v1/users/{user_id}/change-password
   */
  async adminChangePassword(userId: string, newPassword: string): Promise<MessageResponse> {
    const payload: AdminChangePasswordRequest = {
      new_password: newPassword,
    };
    return apiClient.post<MessageResponse>(`/users/${userId}/change-password`, payload);
  },
};
