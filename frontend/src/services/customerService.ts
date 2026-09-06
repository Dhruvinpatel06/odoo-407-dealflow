import { apiClient } from './apiClient';
import {
  CustomerResponse,
  CustomerDetailResponse,
  CustomerCreateRequest,
  CustomerUpdateRequest,
  BackendQuotationSummary,
  BackendOrderSummary,
  BackendSubscriptionSummary
} from '../types';

export interface ListCustomersParams {
  search?: string;
  customer_tier_id?: string;
  is_active?: boolean;
  skip?: number;
  limit?: number;
}

export const customerService = {
  /**
   * List and search B2B customers:
   * GET /api/v1/customers
   */
  async getCustomers(params?: ListCustomersParams): Promise<CustomerResponse[]> {
    const query = new URLSearchParams();
    if (params?.search) query.append('search', params.search);
    if (params?.customer_tier_id) query.append('customer_tier_id', params.customer_tier_id);
    if (params?.is_active !== undefined) query.append('is_active', String(params.is_active));
    if (params?.skip !== undefined) query.append('skip', String(params.skip));
    if (params?.limit !== undefined) query.append('limit', String(params.limit));

    const qs = query.toString();
    return apiClient.get<CustomerResponse[]>(`/customers${qs ? `?${qs}` : ''}`);
  },

  /**
   * Create new B2B customer:
   * POST /api/v1/customers
   */
  async createCustomer(payload: CustomerCreateRequest): Promise<CustomerResponse> {
    const body: Record<string, any> = {
      name: payload.name.trim(),
      customer_tier_id: payload.customer_tier_id,
      is_active: payload.is_active ?? true,
    };

    if (payload.email && payload.email.trim()) body.email = payload.email.trim();
    if (payload.phone && payload.phone.trim()) body.phone = payload.phone.trim();
    if (payload.billing_address && payload.billing_address.trim()) body.billing_address = payload.billing_address.trim();
    if (payload.shipping_address && payload.shipping_address.trim()) body.shipping_address = payload.shipping_address.trim();

    return apiClient.post<CustomerResponse>('/customers', body);
  },

  /**
   * Get single customer details with tier association:
   * GET /api/v1/customers/{id}
   */
  async getCustomer(id: string): Promise<CustomerDetailResponse> {
    return apiClient.get<CustomerDetailResponse>(`/customers/${id}`);
  },

  /**
   * Update existing customer:
   * PATCH /api/v1/customers/{id}
   */
  async updateCustomer(id: string, payload: CustomerUpdateRequest): Promise<CustomerResponse> {
    return apiClient.patch<CustomerResponse>(`/customers/${id}`, payload);
  },

  /**
   * Deactivate customer (logical deactivation):
   * DELETE /api/v1/customers/{id}
   */
  async deleteCustomer(id: string): Promise<CustomerResponse> {
    return apiClient.delete<CustomerResponse>(`/customers/${id}`);
  },

  /**
   * Get customer quotation history:
   * GET /api/v1/customers/{id}/quotations
   */
  async getCustomerQuotations(
    id: string,
    params?: { skip?: number; limit?: number }
  ): Promise<BackendQuotationSummary[]> {
    const query = new URLSearchParams();
    if (params?.skip !== undefined) query.append('skip', String(params.skip));
    if (params?.limit !== undefined) query.append('limit', String(params.limit));
    const qs = query.toString();

    return apiClient.get<BackendQuotationSummary[]>(`/customers/${id}/quotations${qs ? `?${qs}` : ''}`);
  },

  /**
   * Get customer order history:
   * GET /api/v1/customers/{id}/orders
   */
  async getCustomerOrders(
    id: string,
    params?: { skip?: number; limit?: number }
  ): Promise<BackendOrderSummary[]> {
    const query = new URLSearchParams();
    if (params?.skip !== undefined) query.append('skip', String(params.skip));
    if (params?.limit !== undefined) query.append('limit', String(params.limit));
    const qs = query.toString();

    return apiClient.get<BackendOrderSummary[]>(`/customers/${id}/orders${qs ? `?${qs}` : ''}`);
  },

  /**
   * Get customer subscription history:
   * GET /api/v1/customers/{id}/subscriptions
   */
  async getCustomerSubscriptions(
    id: string,
    params?: { skip?: number; limit?: number }
  ): Promise<BackendSubscriptionSummary[]> {
    const query = new URLSearchParams();
    if (params?.skip !== undefined) query.append('skip', String(params.skip));
    if (params?.limit !== undefined) query.append('limit', String(params.limit));
    const qs = query.toString();

    return apiClient.get<BackendSubscriptionSummary[]>(`/customers/${id}/subscriptions${qs ? `?${qs}` : ''}`);
  },
};
