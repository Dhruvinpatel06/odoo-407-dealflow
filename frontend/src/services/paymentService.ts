import { apiClient } from './apiClient';

// ---------- Types ----------

export interface PaymentDetailResponse {
  id: string;
  invoice_id: string;
  amount: string | number;
  payment_method: string;
  transaction_reference?: string | null;
  status: string;
  created_at: string;
  updated_at?: string;
}

export interface ListPaymentsParams {
  invoice_id?: string;
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

export const paymentService = {
  async listPayments(params?: ListPaymentsParams): Promise<PaymentDetailResponse[]> {
    return apiClient.get<PaymentDetailResponse[]>(`/payments${buildQuery(params)}`);
  },

  async getPayment(id: string): Promise<PaymentDetailResponse> {
    return apiClient.get<PaymentDetailResponse>(`/payments/${id}`);
  },

  async refundPayment(id: string): Promise<PaymentDetailResponse> {
    return apiClient.post<PaymentDetailResponse>(`/payments/${id}/refund`);
  },
};
