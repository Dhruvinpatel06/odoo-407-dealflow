import { apiClient } from './apiClient';

// ---------- Types ----------

export interface SubscriptionResponse {
  id: string;
  order_id: string;
  quotation_line_id?: string;
  customer_id: string;
  customer_name?: string;
  product_id: string;
  product_name?: string;
  plan_id: string;
  plan_name?: string;
  quantity: string | number;
  unit_price: string | number;
  start_date: string;
  next_billing_date: string;
  status: string;
  billing_interval?: string;
  created_at: string;
  updated_at: string;
}

export interface SubscriptionModifyRequest {
  quantity?: number | string;
  plan_id?: string;
  unit_price?: number | string;
  effective_date?: string;
}

export interface SubscriptionCancelRequest {
  reason?: string;
  issue_credit_note?: boolean;
}

export interface ProrationPreviewRequest {
  new_quantity?: number | string;
  new_plan_id?: string;
  new_unit_price?: number | string;
  effective_date?: string;
}

export interface ProrationApplyRequest extends ProrationPreviewRequest {
  issue_credit_note?: boolean;
}

export interface ProrationResponse {
  subscription_id: string;
  current_amount: string | number;
  new_amount: string | number;
  proration_amount: string | number;
  credit_amount?: string | number;
  effective_date: string;
  days_remaining?: number;
  total_days?: number;
}

export interface ListSubscriptionsParams {
  customer_id?: string;
  status?: string;
  order_id?: string;
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

export const subscriptionService = {
  async listSubscriptions(params?: ListSubscriptionsParams): Promise<SubscriptionResponse[]> {
    return apiClient.get<SubscriptionResponse[]>(`/subscriptions${buildQuery(params)}`);
  },

  async getSubscription(id: string): Promise<SubscriptionResponse> {
    return apiClient.get<SubscriptionResponse>(`/subscriptions/${id}`);
  },

  async modifySubscription(id: string, payload: SubscriptionModifyRequest): Promise<SubscriptionResponse> {
    return apiClient.post<SubscriptionResponse>(`/subscriptions/${id}/modify`, payload);
  },

  async cancelSubscription(id: string, payload?: SubscriptionCancelRequest): Promise<SubscriptionResponse> {
    return apiClient.post<SubscriptionResponse>(`/subscriptions/${id}/cancel`, payload || {});
  },

  async pauseSubscription(id: string): Promise<SubscriptionResponse> {
    return apiClient.post<SubscriptionResponse>(`/subscriptions/${id}/pause`);
  },

  async previewProration(id: string, payload: ProrationPreviewRequest): Promise<ProrationResponse> {
    return apiClient.post<ProrationResponse>(`/subscriptions/${id}/proration/preview`, payload);
  },

  async applyProration(id: string, payload: ProrationApplyRequest): Promise<SubscriptionResponse> {
    return apiClient.post<SubscriptionResponse>(`/subscriptions/${id}/proration/apply`, payload);
  },

  async generateCreditNote(id: string): Promise<any> {
    return apiClient.post(`/subscriptions/${id}/credit-note`);
  },
};
