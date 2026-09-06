import { apiClient } from './apiClient';

// ---------- Types ----------

export interface BillingScheduleResponse {
  id: string;
  subscription_id: string;
  scheduled_date: string;
  amount: string | number;
  status: string;
  invoice_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ListBillingSchedulesParams {
  subscription_id?: string;
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

export const billingScheduleService = {
  async listSchedules(params?: ListBillingSchedulesParams): Promise<BillingScheduleResponse[]> {
    return apiClient.get<BillingScheduleResponse[]>(`/billing-schedules${buildQuery(params)}`);
  },

  async getSchedule(id: string): Promise<BillingScheduleResponse> {
    return apiClient.get<BillingScheduleResponse>(`/billing-schedules/${id}`);
  },

  async generateInvoice(id: string): Promise<BillingScheduleResponse> {
    return apiClient.post<BillingScheduleResponse>(`/billing-schedules/${id}/generate-invoice`);
  },

  async cancelSchedule(id: string): Promise<BillingScheduleResponse> {
    return apiClient.post<BillingScheduleResponse>(`/billing-schedules/${id}/cancel`);
  },
};
