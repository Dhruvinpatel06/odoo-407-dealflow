import { apiClient } from './apiClient';

// ---------- Types ----------

export interface OrderResponse {
  id: string;
  order_number: string;
  customer_id: string;
  customer_name?: string;
  quotation_id: string;
  quotation_number?: string;
  status: string;
  total_amount: string | number;
  created_at: string;
  updated_at: string;
}

export interface OrderUpdateRequest {
  status?: string;
}

export interface ListOrdersParams {
  customer_id?: string;
  status?: string;
  skip?: number;
  limit?: number;
}

// ---------- Service ----------

function buildQuery(params?: Record<string, any>): string {
  if (!params) return '';
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  }
  const qs = query.toString();
  return qs ? `?${qs}` : '';
}

export const orderService = {
  async listOrders(params?: ListOrdersParams): Promise<OrderResponse[]> {
    return apiClient.get<OrderResponse[]>(`/orders${buildQuery(params)}`);
  },

  async getOrder(id: string): Promise<OrderResponse> {
    return apiClient.get<OrderResponse>(`/orders/${id}`);
  },

  async updateOrder(id: string, payload: OrderUpdateRequest): Promise<OrderResponse> {
    return apiClient.patch<OrderResponse>(`/orders/${id}`, payload);
  },

  async getAuditLog(id: string): Promise<any[]> {
    return apiClient.get(`/orders/${id}/audit-log`);
  },
};
