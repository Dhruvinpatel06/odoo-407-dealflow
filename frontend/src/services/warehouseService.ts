import { apiClient } from './apiClient';

// ---------- Types ----------

export interface WarehouseResponse {
  id: string;
  name: string;
  code: string;
  address?: string | null;
  shipping_cost_weight: string | number;
  replenishment_enabled: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WarehouseCreateRequest {
  name: string;
  code: string;
  address?: string;
  shipping_cost_weight?: number | string;
  replenishment_enabled?: boolean;
  is_active?: boolean;
}

export interface WarehouseUpdateRequest {
  name?: string;
  code?: string;
  address?: string;
  shipping_cost_weight?: number | string;
  replenishment_enabled?: boolean;
  is_active?: boolean;
}

export interface InventoryResponse {
  id: string;
  warehouse_id: string;
  warehouse_name?: string;
  product_id: string;
  product_name?: string;
  quantity_on_hand: string | number;
  quantity_reserved: string | number;
  quantity_available?: string | number;
  reorder_level: string | number;
  reorder_quantity: string | number;
  created_at?: string;
  updated_at?: string;
}

export interface InventoryUpdateRequest {
  quantity_on_hand?: number | string;
  quantity_reserved?: number | string;
  reorder_level?: number | string;
  reorder_quantity?: number | string;
}

export interface WarehouseInventoryCreateRequest {
  product_id: string;
  quantity_on_hand?: number | string;
  reorder_level?: number | string;
  reorder_quantity?: number | string;
}

export interface ListWarehousesParams {
  is_active?: boolean;
  skip?: number;
  limit?: number;
}

export interface ListInventoryParams {
  warehouse_id?: string;
  product_id?: string;
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

export const warehouseService = {
  // --- Warehouses ---

  async listWarehouses(params?: ListWarehousesParams): Promise<WarehouseResponse[]> {
    return apiClient.get<WarehouseResponse[]>(`/warehouses${buildQuery(params)}`);
  },

  async createWarehouse(payload: WarehouseCreateRequest): Promise<WarehouseResponse> {
    return apiClient.post<WarehouseResponse>('/warehouses', payload);
  },

  async getWarehouse(id: string): Promise<WarehouseResponse> {
    return apiClient.get<WarehouseResponse>(`/warehouses/${id}`);
  },

  async updateWarehouse(id: string, payload: WarehouseUpdateRequest): Promise<WarehouseResponse> {
    return apiClient.patch<WarehouseResponse>(`/warehouses/${id}`, payload);
  },

  async deleteWarehouse(id: string): Promise<WarehouseResponse> {
    return apiClient.delete<WarehouseResponse>(`/warehouses/${id}`);
  },

  async getWarehouseInventory(warehouseId: string, params?: { skip?: number; limit?: number }): Promise<InventoryResponse[]> {
    return apiClient.get<InventoryResponse[]>(`/warehouses/${warehouseId}/inventory${buildQuery(params)}`);
  },

  async configureInventory(warehouseId: string, payload: WarehouseInventoryCreateRequest): Promise<InventoryResponse> {
    return apiClient.post<InventoryResponse>(`/warehouses/${warehouseId}/inventory`, payload);
  },

  // --- Inventory ---

  async listInventory(params?: ListInventoryParams): Promise<InventoryResponse[]> {
    return apiClient.get<InventoryResponse[]>(`/inventory${buildQuery(params)}`);
  },

  async getInventory(id: string): Promise<InventoryResponse> {
    return apiClient.get<InventoryResponse>(`/inventory/${id}`);
  },

  async updateInventory(id: string, payload: InventoryUpdateRequest): Promise<InventoryResponse> {
    return apiClient.patch<InventoryResponse>(`/inventory/${id}`, payload);
  },

  async getProductInventory(productId: string): Promise<InventoryResponse[]> {
    return apiClient.get<InventoryResponse[]>(`/inventory/product/${productId}`);
  },
};
