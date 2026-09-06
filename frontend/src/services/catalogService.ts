import { apiClient } from './apiClient';
import {
  CategoryResponse,
  CategoryCreateRequest,
  CategoryUpdateRequest,
  ProductItemResponse,
  ProductCreateRequest,
  ProductUpdateRequest,
  VariantResponse,
  VariantCreateRequest,
  VariantUpdateRequest
} from '../types';

export const catalogService = {
  // --- Product Categories ---

  async getCategories(): Promise<CategoryResponse[]> {
    return apiClient.get<CategoryResponse[]>('/product-categories');
  },

  async createCategory(payload: CategoryCreateRequest): Promise<CategoryResponse> {
    return apiClient.post<CategoryResponse>('/product-categories', payload);
  },

  async getCategory(id: string): Promise<CategoryResponse> {
    return apiClient.get<CategoryResponse>(`/product-categories/${id}`);
  },

  async updateCategory(id: string, payload: CategoryUpdateRequest): Promise<CategoryResponse> {
    return apiClient.patch<CategoryResponse>(`/product-categories/${id}`, payload);
  },

  async deleteCategory(id: string): Promise<CategoryResponse> {
    return apiClient.delete<CategoryResponse>(`/product-categories/${id}`);
  },

  // --- Products ---

  async getProducts(): Promise<ProductItemResponse[]> {
    return apiClient.get<ProductItemResponse[]>('/products');
  },

  async createProduct(payload: ProductCreateRequest): Promise<ProductItemResponse> {
    return apiClient.post<ProductItemResponse>('/products', payload);
  },

  async getProduct(id: string): Promise<ProductItemResponse> {
    return apiClient.get<ProductItemResponse>(`/products/${id}`);
  },

  async updateProduct(id: string, payload: ProductUpdateRequest): Promise<ProductItemResponse> {
    return apiClient.patch<ProductItemResponse>(`/products/${id}`, payload);
  },

  async deleteProduct(id: string): Promise<ProductItemResponse> {
    return apiClient.delete<ProductItemResponse>(`/products/${id}`);
  },

  async getProductVariants(productId: string): Promise<VariantResponse[]> {
    return apiClient.get<VariantResponse[]>(`/products/${productId}/variants`);
  },

  // --- Product Variants ---

  async createVariant(productId: string, payload: VariantCreateRequest): Promise<VariantResponse> {
    return apiClient.post<VariantResponse>(`/products/${productId}/variants`, payload);
  },

  async getVariant(id: string): Promise<VariantResponse> {
    return apiClient.get<VariantResponse>(`/variants/${id}`);
  },

  async updateVariant(id: string, payload: VariantUpdateRequest): Promise<VariantResponse> {
    return apiClient.patch<VariantResponse>(`/variants/${id}`, payload);
  },

  async deleteVariant(id: string): Promise<VariantResponse> {
    return apiClient.delete<VariantResponse>(`/variants/${id}`);
  },
};
