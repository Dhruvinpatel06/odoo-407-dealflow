import { apiClient } from './apiClient';

// ---------- Types ----------

export interface QuotationCreateRequest {
  customer_id: string;
  valid_until?: string | null;
}

export interface QuotationUpdateRequest {
  valid_until?: string | null;
}

export interface QuotationLineCreateRequest {
  product_id: string;
  variant_id?: string | null;
  quantity: number | string;
  unit_price?: number | string | null;
  discount_percent?: number | string;
  tax_rate?: number | string;
  description?: string | null;
}

export interface QuotationLineUpdateRequest {
  quantity?: number | string | null;
  unit_price?: number | string | null;
  discount_percent?: number | string | null;
  tax_rate?: number | string | null;
  description?: string | null;
}

export interface QuotationLineResponse {
  id: string;
  quotation_id: string;
  product_id: string;
  variant_id?: string | null;
  product_name?: string;
  product_sku?: string;
  category_name?: string;
  quantity: string | number;
  unit_price: string | number;
  cost_price?: string | number;
  discount_percent: string | number;
  discount_amount?: string | number;
  tax_rate: string | number;
  tax_amount?: string | number;
  line_total: string | number;
  margin_amount?: string | number;
  margin_percent?: string | number;
  allowed_discount_ceiling?: string | number;
  discount_excess_percent?: string | number;
  is_subscription?: boolean;
  description?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface QuotationResponse {
  id: string;
  quotation_number: string;
  customer_id: string;
  customer_name?: string;
  customer_tier_name?: string;
  sales_rep_id: string;
  sales_rep_name?: string;
  status: string;
  subtotal: string | number;
  discount_amount: string | number;
  order_discount_percent: string | number;
  tax_amount: string | number;
  total_amount: string | number;
  total_cost: string | number;
  margin_amount: string | number;
  margin_percent: string | number;
  risk_score: string | number;
  risk_status?: string;
  approval_required: boolean;
  approval_level?: string;
  last_activity_at?: string;
  valid_until?: string | null;
  created_at: string;
  updated_at: string;
  lines?: QuotationLineResponse[];
  risk_reasons?: string[];
}

export interface QuotationRiskResponse {
  quotation_id: string;
  risk_score: string | number;
  risk_status: string;
  approval_required: boolean;
  approval_level: string;
  reasons: string[];
  line_details?: Array<{
    line_id: string;
    product_name: string;
    discount_percent: string | number;
    allowed_ceiling: string | number;
    excess_percent: string | number;
  }>;
}

export interface ListQuotationsParams {
  status?: string;
  customer_id?: string;
  sales_rep_id?: string;
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

export const quotationService = {
  // --- Quotations ---

  async listQuotations(params?: ListQuotationsParams): Promise<QuotationResponse[]> {
    return apiClient.get<QuotationResponse[]>(`/quotations${buildQuery(params)}`);
  },

  async createQuotation(payload: QuotationCreateRequest): Promise<QuotationResponse> {
    return apiClient.post<QuotationResponse>('/quotations', payload);
  },

  async getQuotation(id: string): Promise<QuotationResponse> {
    return apiClient.get<QuotationResponse>(`/quotations/${id}`);
  },

  async updateQuotation(id: string, payload: QuotationUpdateRequest): Promise<QuotationResponse> {
    return apiClient.patch<QuotationResponse>(`/quotations/${id}`, payload);
  },

  async deleteQuotation(id: string): Promise<void> {
    return apiClient.delete<void>(`/quotations/${id}`);
  },

  // --- Lines ---

  async getLines(quotationId: string): Promise<QuotationLineResponse[]> {
    return apiClient.get<QuotationLineResponse[]>(`/quotations/${quotationId}/lines`);
  },

  async addLine(quotationId: string, payload: QuotationLineCreateRequest): Promise<QuotationLineResponse> {
    return apiClient.post<QuotationLineResponse>(`/quotations/${quotationId}/lines`, payload);
  },

  async updateLine(quotationId: string, lineId: string, payload: QuotationLineUpdateRequest): Promise<QuotationLineResponse> {
    return apiClient.patch<QuotationLineResponse>(`/quotations/${quotationId}/lines/${lineId}`, payload);
  },

  async deleteLine(quotationId: string, lineId: string): Promise<void> {
    return apiClient.delete<void>(`/quotations/${quotationId}/lines/${lineId}`);
  },

  // --- Quotation Actions ---

  async recalculate(id: string): Promise<QuotationResponse> {
    return apiClient.post<QuotationResponse>(`/quotations/${id}/recalculate`);
  },

  async getRisk(id: string): Promise<QuotationRiskResponse> {
    return apiClient.get<QuotationRiskResponse>(`/quotations/${id}/risk`);
  },

  async submit(id: string): Promise<QuotationResponse> {
    return apiClient.post<QuotationResponse>(`/quotations/${id}/submit`);
  },

  async send(id: string): Promise<QuotationResponse> {
    return apiClient.post<QuotationResponse>(`/quotations/${id}/send`);
  },

  async returnForRevision(id: string): Promise<QuotationResponse> {
    return apiClient.post<QuotationResponse>(`/quotations/${id}/return-for-revision`);
  },

  async confirm(id: string): Promise<QuotationResponse> {
    return apiClient.post<QuotationResponse>(`/quotations/${id}/confirm`);
  },

  async getOrder(id: string): Promise<any> {
    return apiClient.get(`/quotations/${id}/order`);
  },

  async getApprovals(id: string): Promise<any[]> {
    return apiClient.get(`/quotations/${id}/approvals`);
  },

  async getAuditLog(id: string): Promise<any[]> {
    return apiClient.get(`/quotations/${id}/audit-log`);
  },
};
