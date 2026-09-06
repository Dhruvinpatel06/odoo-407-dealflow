import { apiClient } from './apiClient';

// ---------- Types ----------

export interface SubscriptionPlanResponse {
  id: string;
  name: string;
  billing_interval: string;
  interval_count: number;
  proration_method: string;
  cancellation_policy: string;
  refund_policy: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SubscriptionPlanCreateRequest {
  name: string;
  billing_interval: 'MONTHLY' | 'QUARTERLY' | 'YEARLY';
  interval_count?: number;
  proration_method?: string;
  cancellation_policy?: string;
  refund_policy?: string;
  is_active?: boolean;
}

export interface SubscriptionPlanUpdateRequest {
  name?: string;
  billing_interval?: string;
  interval_count?: number;
  proration_method?: string;
  cancellation_policy?: string;
  refund_policy?: string;
  is_active?: boolean;
}

export interface ListSubscriptionPlansParams {
  is_active?: boolean;
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

export const subscriptionPlanService = {
  async listPlans(params?: ListSubscriptionPlansParams): Promise<SubscriptionPlanResponse[]> {
    return apiClient.get<SubscriptionPlanResponse[]>(`/subscription-plans${buildQuery(params)}`);
  },

  async createPlan(payload: SubscriptionPlanCreateRequest): Promise<SubscriptionPlanResponse> {
    return apiClient.post<SubscriptionPlanResponse>('/subscription-plans', payload);
  },

  async getPlan(id: string): Promise<SubscriptionPlanResponse> {
    return apiClient.get<SubscriptionPlanResponse>(`/subscription-plans/${id}`);
  },

  async updatePlan(id: string, payload: SubscriptionPlanUpdateRequest): Promise<SubscriptionPlanResponse> {
    return apiClient.patch<SubscriptionPlanResponse>(`/subscription-plans/${id}`, payload);
  },

  async deletePlan(id: string): Promise<SubscriptionPlanResponse> {
    return apiClient.delete<SubscriptionPlanResponse>(`/subscription-plans/${id}`);
  },
};
