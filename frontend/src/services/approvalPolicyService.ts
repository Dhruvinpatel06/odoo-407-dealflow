import { apiClient } from './apiClient';

// ---------- Types ----------

export interface ApprovalPolicyResponse {
  id: string;
  name: string;
  min_risk_score: string | number;
  max_risk_score?: string | number | null;
  requires_manager: boolean;
  requires_finance: boolean;
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApprovalPolicyCreateRequest {
  name: string;
  min_risk_score: number | string;
  max_risk_score?: number | string | null;
  requires_manager?: boolean;
  requires_finance?: boolean;
  priority?: number;
  is_active?: boolean;
}

export interface ApprovalPolicyUpdateRequest {
  name?: string;
  min_risk_score?: number | string;
  max_risk_score?: number | string | null;
  requires_manager?: boolean;
  requires_finance?: boolean;
  priority?: number;
  is_active?: boolean;
}

export interface ListApprovalPoliciesParams {
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

export const approvalPolicyService = {
  async listPolicies(params?: ListApprovalPoliciesParams): Promise<ApprovalPolicyResponse[]> {
    return apiClient.get<ApprovalPolicyResponse[]>(`/approval-policies${buildQuery(params)}`);
  },

  async createPolicy(payload: ApprovalPolicyCreateRequest): Promise<ApprovalPolicyResponse> {
    return apiClient.post<ApprovalPolicyResponse>('/approval-policies', payload);
  },

  async getPolicy(id: string): Promise<ApprovalPolicyResponse> {
    return apiClient.get<ApprovalPolicyResponse>(`/approval-policies/${id}`);
  },

  async updatePolicy(id: string, payload: ApprovalPolicyUpdateRequest): Promise<ApprovalPolicyResponse> {
    return apiClient.patch<ApprovalPolicyResponse>(`/approval-policies/${id}`, payload);
  },

  async deletePolicy(id: string): Promise<ApprovalPolicyResponse> {
    return apiClient.delete<ApprovalPolicyResponse>(`/approval-policies/${id}`);
  },
};
