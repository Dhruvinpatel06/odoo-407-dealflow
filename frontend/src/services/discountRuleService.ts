import { apiClient } from './apiClient';

// ---------- Types ----------

export interface DiscountRuleResponse {
  id: string;
  customer_tier_id?: string | null;
  customer_tier_name?: string;
  category_id?: string | null;
  category_name?: string;
  max_discount_percent: string | number;
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DiscountRuleCreateRequest {
  customer_tier_id?: string;
  category_id?: string;
  max_discount_percent: number | string;
  priority?: number;
  is_active?: boolean;
}

export interface DiscountRuleUpdateRequest {
  customer_tier_id?: string;
  category_id?: string;
  max_discount_percent?: number | string;
  priority?: number;
  is_active?: boolean;
}

export interface ListDiscountRulesParams {
  customer_tier_id?: string;
  category_id?: string;
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

export const discountRuleService = {
  async listRules(params?: ListDiscountRulesParams): Promise<DiscountRuleResponse[]> {
    return apiClient.get<DiscountRuleResponse[]>(`/discount-rules${buildQuery(params)}`);
  },

  async createRule(payload: DiscountRuleCreateRequest): Promise<DiscountRuleResponse> {
    return apiClient.post<DiscountRuleResponse>('/discount-rules', payload);
  },

  async getRule(id: string): Promise<DiscountRuleResponse> {
    return apiClient.get<DiscountRuleResponse>(`/discount-rules/${id}`);
  },

  async updateRule(id: string, payload: DiscountRuleUpdateRequest): Promise<DiscountRuleResponse> {
    return apiClient.patch<DiscountRuleResponse>(`/discount-rules/${id}`, payload);
  },

  async deleteRule(id: string): Promise<DiscountRuleResponse> {
    return apiClient.delete<DiscountRuleResponse>(`/discount-rules/${id}`);
  },
};
