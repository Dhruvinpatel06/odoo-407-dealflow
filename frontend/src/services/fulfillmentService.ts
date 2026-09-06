import { apiClient } from './apiClient';

// ---------- Types ----------

export interface FulfillmentAllocationResponse {
  id: string;
  quotation_line_id?: string;
  warehouse_id: string;
  warehouse_name?: string;
  product_id?: string;
  product_name?: string;
  quantity_allocated: string | number;
  status?: string;
  created_at?: string;
  updated_at?: string;
}

export interface FulfillmentResponse {
  order_id: string;
  order_number?: string;
  customer_name?: string;
  order_status?: string;
  status?: string;
  allocations?: FulfillmentAllocationResponse[];
  backorders?: BackorderResponse[];
  total_quantity_required?: string | number;
  total_quantity_allocated?: string | number;
  total_quantity_fulfilled?: string | number;
  total_quantity_backordered?: string | number;
  estimated_shipment_count?: number;
  estimated_shipping_cost?: string | number;
  total_shipments?: number;
  total_shipping_cost?: string | number;
  backorder_count?: number;
  is_split?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface FulfillmentOverrideItem {
  quotation_line_id: string;
  warehouse_id: string;
  quantity_allocated: number | string;
}

export interface FulfillmentOverrideRequest {
  allocations: FulfillmentOverrideItem[];
}

export interface AllocationUpdateRequest {
  warehouse_id?: string;
  quantity_allocated?: number | string;
}

export interface BackorderResponse {
  id: string;
  order_id: string;
  order_number?: string;
  quotation_line_id?: string;
  product_id?: string;
  product_name?: string;
  quantity_backordered: string | number;
  quantity_fulfilled?: string | number;
  status: string;
  created_at?: string;
  updated_at?: string;
}

export interface ListBackordersParams {
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

export const fulfillmentService = {
  // --- Order Fulfillment ---

  async getFulfillment(orderId: string): Promise<FulfillmentResponse> {
    return apiClient.get<FulfillmentResponse>(`/orders/${orderId}/fulfillment`);
  },

  async suggestFulfillment(orderId: string): Promise<FulfillmentResponse> {
    return apiClient.post<FulfillmentResponse>(`/orders/${orderId}/fulfillment/suggest`);
  },

  async acceptFulfillment(orderId: string): Promise<FulfillmentResponse> {
    return apiClient.post<FulfillmentResponse>(`/orders/${orderId}/fulfillment/accept`);
  },

  async getAllocations(orderId: string): Promise<FulfillmentAllocationResponse[]> {
    return apiClient.get<FulfillmentAllocationResponse[]>(`/orders/${orderId}/fulfillment/allocations`);
  },

  async updateAllocation(orderId: string, allocationId: string, payload: AllocationUpdateRequest): Promise<FulfillmentAllocationResponse> {
    return apiClient.patch<FulfillmentAllocationResponse>(`/orders/${orderId}/fulfillment/allocations/${allocationId}`, payload);
  },

  async overrideFulfillment(orderId: string, payload: FulfillmentOverrideRequest): Promise<FulfillmentResponse> {
    return apiClient.post<FulfillmentResponse>(`/orders/${orderId}/fulfillment/override`, payload);
  },

  async overrideAllocations(orderId: string, payload: FulfillmentOverrideRequest): Promise<FulfillmentResponse> {
    return this.overrideFulfillment(orderId, payload);
  },

  async completeFulfillment(orderId: string): Promise<FulfillmentResponse> {
    return apiClient.post<FulfillmentResponse>(`/orders/${orderId}/fulfillment/complete`);
  },

  async getOrderBackorders(orderId: string): Promise<BackorderResponse[]> {
    return apiClient.get<BackorderResponse[]>(`/orders/${orderId}/backorders`);
  },

  // --- Backorders ---

  async listBackorders(params?: ListBackordersParams): Promise<BackorderResponse[]> {
    return apiClient.get<BackorderResponse[]>(`/backorders${buildQuery(params)}`);
  },

  async getBackorder(id: string): Promise<BackorderResponse> {
    return apiClient.get<BackorderResponse>(`/backorders/${id}`);
  },

  async consolidateBackorder(id: string): Promise<BackorderResponse> {
    return apiClient.post<BackorderResponse>(`/backorders/${id}/consolidate`);
  },

  async cancelBackorder(id: string): Promise<BackorderResponse> {
    return apiClient.post<BackorderResponse>(`/backorders/${id}/cancel`);
  },
};
