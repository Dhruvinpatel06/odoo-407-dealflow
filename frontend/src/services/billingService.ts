import { apiClient } from './apiClient';

// ---------- Types ----------

export interface BillingStateResponse {
  order_id: string;
  one_time_invoices?: any[];
  recurring_subscriptions?: any[];
  billing_schedules?: any[];
  total_billed?: string | number;
  total_paid?: string | number;
  balance_due?: string | number;
}

export interface CreditNoteRequest {
  amount: number | string;
  reason?: string;
}

// ---------- Service ----------

export const billingService = {
  async getOrderBilling(orderId: string): Promise<BillingStateResponse> {
    return apiClient.get<BillingStateResponse>(`/orders/${orderId}/billing`);
  },

  async generateBilling(orderId: string): Promise<BillingStateResponse> {
    return apiClient.post<BillingStateResponse>(`/orders/${orderId}/billing/generate`);
  },

  async createCreditNote(orderId: string, payload: CreditNoteRequest): Promise<any> {
    return apiClient.post(`/orders/${orderId}/credit-notes`, payload);
  },
};
