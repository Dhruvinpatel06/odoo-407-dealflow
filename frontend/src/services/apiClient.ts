/**
 * Centralized API Client for DealFlow360
 * Base Prefix: /api/v1
 * Authoritative Backend: FastAPI
 */

export const API_BASE_URL = (
  import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
).replace(/\/+$/, '');

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// In-memory access token storage (short-lived JWT, never persisted to localStorage/sessionStorage)
let inMemoryAccessToken: string | null = null;
let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

export const tokenStore = {
  get(): string | null {
    return inMemoryAccessToken;
  },
  set(token: string | null): void {
    inMemoryAccessToken = token;
  },
  clear(): void {
    inMemoryAccessToken = null;
  }
};

/**
 * Parses FastAPI response error payloads (string, dict with detail, or validation error list).
 */
export async function parseApiError(response: Response): Promise<{ message: string; details: unknown }> {
  let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
  let details: unknown = null;

  try {
    const errorData = await response.json();
    details = errorData;

    if (typeof errorData?.detail === 'string') {
      errorMessage = errorData.detail;
    } else if (Array.isArray(errorData?.detail)) {
      // FastAPI 422 Validation Error structure: [{ loc: [...], msg: "...", type: "..." }]
      errorMessage = errorData.detail
        .map((item: any) => {
          const loc = Array.isArray(item?.loc) ? item.loc.slice(1).join('.') : '';
          return loc ? `${loc}: ${item.msg || 'Invalid input'}` : item.msg || 'Validation error';
        })
        .join('; ');
    } else if (typeof errorData?.message === 'string') {
      errorMessage = errorData.message;
    }
  } catch {
    // Non-JSON response body
  }

  // Common status messages if detail was blank
  if (!errorMessage || errorMessage.startsWith('HTTP Error')) {
    switch (response.status) {
      case 400:
        errorMessage = 'Bad Request. Please verify your input.';
        break;
      case 401:
        errorMessage = 'Unauthorized. Please sign in with valid credentials.';
        break;
      case 403:
        errorMessage = 'Forbidden. You do not have permission to perform this action.';
        break;
      case 404:
        errorMessage = 'The requested resource was not found on the server.';
        break;
      case 409:
        errorMessage = 'Conflict. The resource already exists or has conflicting state.';
        break;
      case 422:
        errorMessage = 'Unprocessable Entity. Validation failed on the server.';
        break;
      case 500:
      default:
        if (response.status >= 500) {
          errorMessage = 'Server error. The service is temporarily unavailable.';
        }
        break;
    }
  }

  return { message: errorMessage, details };
}

/**
 * Attempts silent token refresh via HttpOnly refresh cookie:
 * POST /api/v1/auth/refresh
 */
async function attemptRefresh(): Promise<string | null> {
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      });

      if (!response.ok) {
        tokenStore.clear();
        return null;
      }

      const data = await response.json();
      if (data?.access_token) {
        tokenStore.set(data.access_token);
        return data.access_token;
      }
      return null;
    } catch {
      tokenStore.clear();
      return null;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
  retryOn401?: boolean;
}

/**
 * Centralized API requester with authentication, auto-refresh on 401,
 * and standardized error parsing.
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { skipAuth = false, retryOn401 = true, ...fetchOptions } = options;

  const url = endpoint.startsWith('http')
    ? endpoint
    : `${API_BASE_URL}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;

  const headers = new Headers(fetchOptions.headers || {});
  if (!headers.has('Content-Type') && !(fetchOptions.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const token = tokenStore.get();
  if (!skipAuth && token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...fetchOptions,
      headers,
      credentials: 'include', // Ensures HttpOnly refresh cookie is sent
    });
  } catch (networkError: unknown) {
    throw new ApiError(
      0,
      'Unable to connect to the DealFlow360 backend server. Please ensure the backend is running.',
      networkError
    );
  }

  // Handle 401 Unauthorized with token refresh rotation
  if (response.status === 401 && retryOn401 && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/refresh')) {
    const newToken = await attemptRefresh();
    if (newToken) {
      headers.set('Authorization', `Bearer ${newToken}`);
      try {
        response = await fetch(url, {
          ...fetchOptions,
          headers,
          credentials: 'include',
        });
      } catch (retryError: unknown) {
        throw new ApiError(0, 'Network error during retried request.', retryError);
      }
    }
  }

  if (!response.ok) {
    const { message, details } = await parseApiError(response);
    throw new ApiError(response.status, message, details);
  }

  // For 204 No Content or empty responses
  if (response.status === 204) {
    return {} as T;
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return await response.json();
  }

  return (await response.text()) as unknown as T;
}

export const apiClient = {
  get: <T>(endpoint: string, options?: RequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: 'GET' }),

  post: <T>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),

  patch: <T>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),

  delete: <T>(endpoint: string, options?: RequestOptions) =>
    apiRequest<T>(endpoint, { ...options, method: 'DELETE' }),

  token: tokenStore,
};
