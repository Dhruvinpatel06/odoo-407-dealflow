import { apiClient } from './apiClient';
import {
  CustomerTierResponse,
  CustomerTierCreateRequest,
  CustomerTierUpdateRequest
} from '../types';

export interface ListCustomerTiersParams {
  is_active?: boolean;
  skip?: number;
  limit?: number;
}

export const customerTierService = {
  /**
   * List customer tiers:
   * GET /api/v1/customer-tiers
   */
  async getCustomerTiers(params?: ListCustomerTiersParams): Promise<CustomerTierResponse[]> {
    const query = new URLSearchParams();
    if (params?.is_active !== undefined) query.append('is_active', String(params.is_active));
    if (params?.skip !== undefined) query.append('skip', String(params.skip));
    if (params?.limit !== undefined) query.append('limit', String(params.limit));

    const qs = query.toString();
    return apiClient.get<CustomerTierResponse[]>(`/customer-tiers${qs ? `?${qs}` : ''}`);
  },

  /**
   * Create new customer tier:
   * POST /api/v1/customer-tiers
   */
  async createCustomerTier(payload: CustomerTierCreateRequest): Promise<CustomerTierResponse> {
    const body: Record<string, any> = {
      name: payload.name.trim(),
      default_discount_limit: typeof payload.default_discount_limit === 'string'
        ? parseFloat(payload.default_discount_limit) || 0
        : payload.default_discount_limit,
      is_active: payload.is_active ?? true,
    };

    if (payload.description && payload.description.trim()) {
      body.description = payload.description.trim();
    }

    return apiClient.post<CustomerTierResponse>('/customer-tiers', body);
  },

  /**
   * Retrieve customer tier by ID:
   * GET /api/v1/customer-tiers/{id}
   */
  async getCustomerTier(id: string): Promise<CustomerTierResponse> {
    return apiClient.get<CustomerTierResponse>(`/customer-tiers/${id}`);
  },

  /**
   * Update customer tier configuration:
   * PATCH /api/v1/customer-tiers/{id}
   */
  async updateCustomerTier(
    id: string,
    payload: CustomerTierUpdateRequest
  ): Promise<CustomerTierResponse> {
    const body: Record<string, any> = {};
    if (payload.name !== undefined) body.name = payload.name;
    if (payload.description !== undefined) body.description = payload.description;
    if (payload.default_discount_limit !== undefined) {
      body.default_discount_limit = typeof payload.default_discount_limit === 'string'
        ? parseFloat(payload.default_discount_limit) || 0
        : payload.default_discount_limit;
    }
    if (payload.is_active !== undefined) body.is_active = payload.is_active;

    return apiClient.patch<CustomerTierResponse>(`/customer-tiers/${id}`, body);
  },

  /**
   * Deactivate customer tier:
   * DELETE /api/v1/customer-tiers/{id}
   */
  async deleteCustomerTier(id: string): Promise<CustomerTierResponse> {
    return apiClient.delete<CustomerTierResponse>(`/customer-tiers/${id}`);
  },
};
