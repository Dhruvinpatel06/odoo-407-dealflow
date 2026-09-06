import { apiClient } from './apiClient';

// ---------- Types ----------

export interface PriceListResponse {
  id: string;
  name: string;
  customer_tier_id?: string | null;
  currency: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PriceListCreateRequest {
  name: string;
  customer_tier_id?: string;
  currency?: string;
  is_active?: boolean;
}

export interface PriceListUpdateRequest {
  name?: string;
  customer_tier_id?: string;
  currency?: string;
  is_active?: boolean;
}

export interface PriceListItemResponse {
  id: string;
  price_list_id: string;
  product_id: string;
  product_name?: string;
  variant_id?: string | null;
  price: string | number;
  created_at?: string;
  updated_at?: string;
}

export interface PriceListItemCreateRequest {
  product_id: string;
  variant_id?: string;
  price: number | string;
}

export interface PriceListItemUpdateRequest {
  variant_id?: string;
  price?: number | string;
}

export interface PriceResolveRequest {
  product_id: string;
  variant_id?: string;
  customer_id?: string;
  customer_tier_id?: string;
  currency?: string;
  price_list_id?: string;
}

export interface PriceResolveResponse {
  product_id: string;
  variant_id?: string | null;
  resolved_price: string | number;
  source: string;
  price_list_id?: string | null;
  currency: string;
}

export interface ListPriceListsParams {
  customer_tier_id?: string;
  currency?: string;
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

export const pricingService = {
  // --- Price Lists ---

  async listPriceLists(params?: ListPriceListsParams): Promise<PriceListResponse[]> {
    return apiClient.get<PriceListResponse[]>(`/price-lists${buildQuery(params)}`);
  },

  async createPriceList(payload: PriceListCreateRequest): Promise<PriceListResponse> {
    return apiClient.post<PriceListResponse>('/price-lists', payload);
  },

  async getPriceList(id: string): Promise<PriceListResponse> {
    return apiClient.get<PriceListResponse>(`/price-lists/${id}`);
  },

  async updatePriceList(id: string, payload: PriceListUpdateRequest): Promise<PriceListResponse> {
    return apiClient.patch<PriceListResponse>(`/price-lists/${id}`, payload);
  },

  async deletePriceList(id: string): Promise<PriceListResponse> {
    return apiClient.delete<PriceListResponse>(`/price-lists/${id}`);
  },

  // --- Price List Items ---

  async listItems(priceListId: string, params?: { skip?: number; limit?: number }): Promise<PriceListItemResponse[]> {
    return apiClient.get<PriceListItemResponse[]>(`/price-lists/${priceListId}/items${buildQuery(params)}`);
  },

  async addItem(priceListId: string, payload: PriceListItemCreateRequest): Promise<PriceListItemResponse> {
    return apiClient.post<PriceListItemResponse>(`/price-lists/${priceListId}/items`, payload);
  },

  async updateItem(priceListId: string, itemId: string, payload: PriceListItemUpdateRequest): Promise<PriceListItemResponse> {
    return apiClient.patch<PriceListItemResponse>(`/price-lists/${priceListId}/items/${itemId}`, payload);
  },

  async deleteItem(priceListId: string, itemId: string): Promise<void> {
    return apiClient.delete<void>(`/price-lists/${priceListId}/items/${itemId}`);
  },

  // --- Price Resolution ---

  async resolvePrice(payload: PriceResolveRequest): Promise<PriceResolveResponse> {
    return apiClient.post<PriceResolveResponse>('/pricing/resolve', payload);
  },
};
