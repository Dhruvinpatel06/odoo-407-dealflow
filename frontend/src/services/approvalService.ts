import { apiClient } from './apiClient';

// ---------- Types ----------

export interface ApprovalStepResponse {
  id: string;
  step_number: number;
  role_required: string;
  reviewer_id?: string | null;
  reviewer_name?: string | null;
  status: string;
  comment?: string | null;
  decided_at?: string | null;
}

export interface ApprovalInstanceResponse {
  id: string;
  quotation_id: string;
  quotation_number?: string;
  customer_name?: string;
  sales_rep_name?: string;
  total_amount?: string | number;
  risk_score?: string | number;
  status: string;
  steps?: ApprovalStepResponse[];
  created_at: string;
  updated_at: string;
  reasons?: string[];
}

export interface ApprovalActionRequest {
  comment?: string;
}

export interface ListApprovalsParams {
  status?: string;
  quotation_id?: string;
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

export const approvalService = {
  async listApprovals(params?: ListApprovalsParams): Promise<ApprovalInstanceResponse[]> {
    return apiClient.get<ApprovalInstanceResponse[]>(`/approvals${buildQuery(params)}`);
  },

  async listPending(): Promise<ApprovalInstanceResponse[]> {
    return apiClient.get<ApprovalInstanceResponse[]>('/approvals/pending');
  },

  async getApproval(id: string): Promise<ApprovalInstanceResponse> {
    return apiClient.get<ApprovalInstanceResponse>(`/approvals/${id}`);
  },

  async approve(id: string, payload?: ApprovalActionRequest): Promise<ApprovalInstanceResponse> {
    return apiClient.post<ApprovalInstanceResponse>(`/approvals/${id}/approve`, payload || {});
  },

  async reject(id: string, payload?: ApprovalActionRequest): Promise<ApprovalInstanceResponse> {
    return apiClient.post<ApprovalInstanceResponse>(`/approvals/${id}/reject`, payload || {});
  },

  async returnForRevision(id: string, payload?: ApprovalActionRequest): Promise<ApprovalInstanceResponse> {
    return apiClient.post<ApprovalInstanceResponse>(`/approvals/${id}/return-for-revision`, payload || {});
  },

  async getAuditLog(id: string): Promise<any[]> {
    return apiClient.get(`/approvals/${id}/audit-log`);
  },
};
