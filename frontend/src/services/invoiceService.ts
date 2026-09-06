import { apiClient } from './apiClient';

// ---------- Types ----------

export interface InvoiceResponse {
  id: string;
  invoice_number?: string;
  order_id: string;
  customer_name?: string;
  invoice_type: string;
  amount: string | number;
  paid_amount?: string | number;
  balance_due?: string | number;
  status: string;
  due_date?: string | null;
  issued_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaymentResponse {
  id: string;
  invoice_id: string;
  amount: string | number;
  payment_method: string;
  transaction_reference?: string | null;
  status: string;
  created_at: string;
  updated_at?: string;
}

export interface RecordPaymentRequest {
  amount: number | string;
  payment_method: string;
  transaction_reference?: string | null;
}

export interface ListInvoicesParams {
  order_id?: string;
  status?: string;
  invoice_type?: string;
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

export const invoiceService = {
  async listInvoices(params?: ListInvoicesParams): Promise<InvoiceResponse[]> {
    return apiClient.get<InvoiceResponse[]>(`/invoices${buildQuery(params)}`);
  },

  async getInvoice(id: string): Promise<InvoiceResponse> {
    return apiClient.get<InvoiceResponse>(`/invoices/${id}`);
  },

  async issueInvoice(id: string): Promise<InvoiceResponse> {
    return apiClient.post<InvoiceResponse>(`/invoices/${id}/issue`);
  },

  async cancelInvoice(id: string): Promise<InvoiceResponse> {
    return apiClient.post<InvoiceResponse>(`/invoices/${id}/cancel`);
  },

  async getPayments(invoiceId: string): Promise<PaymentResponse[]> {
    return apiClient.get<PaymentResponse[]>(`/invoices/${invoiceId}/payments`);
  },

  async recordPayment(invoiceId: string, payload: RecordPaymentRequest): Promise<PaymentResponse> {
    return apiClient.post<PaymentResponse>(`/invoices/${invoiceId}/payments`, payload);
  },

  async getCreditNotes(invoiceId: string): Promise<InvoiceResponse[]> {
    return apiClient.get<InvoiceResponse[]>(`/invoices/${invoiceId}/credit-notes`);
  },
};
