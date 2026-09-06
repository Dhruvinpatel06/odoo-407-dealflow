/**
 * DealFlow360 API Service Layer
 * Base URL: /api/v1
 * Authoritative Backend: FastAPI
 */

export { API_BASE_URL, apiClient, ApiError } from './apiClient';
export { authService, AuthError } from './authService';
export { userService, UserAdminError } from './userService';
export { customerService } from './customerService';
export { customerTierService } from './customerTierService';
export { catalogService } from './catalogService';

export const queryKeys = {
  auth: {
    me: ['auth', 'me'] as const,
  },
  users: {
    all: ['users'] as const,
    list: (params?: Record<string, any>) => ['users', 'list', params] as const,
    detail: (id: string) => ['users', 'detail', id] as const,
    approvers: ['users', 'approvers'] as const,
  },
  customers: {
    all: ['customers'] as const,
    list: (params?: Record<string, any>) => ['customers', 'list', params] as const,
    detail: (id: string) => ['customers', 'detail', id] as const,
    quotations: (id: string) => ['customers', id, 'quotations'] as const,
    orders: (id: string) => ['customers', id, 'orders'] as const,
    subscriptions: (id: string) => ['customers', id, 'subscriptions'] as const,
  },
  customerTiers: {
    all: ['customer-tiers'] as const,
    list: (params?: Record<string, any>) => ['customer-tiers', 'list', params] as const,
    detail: (id: string) => ['customer-tiers', 'detail', id] as const,
  },
  productCategories: {
    all: ['product-categories'] as const,
    list: (params?: Record<string, any>) => ['product-categories', 'list', params] as const,
    detail: (id: string) => ['product-categories', 'detail', id] as const,
  },
  products: {
    all: ['products'] as const,
    list: (params?: Record<string, any>) => ['products', 'list', params] as const,
    detail: (id: string) => ['products', 'detail', id] as const,
    variants: (productId: string) => ['products', productId, 'variants'] as const,
  },
  variants: {
    all: ['variants'] as const,
    detail: (id: string) => ['variants', 'detail', id] as const,
  },
  quotations: {
    all: ['quotations'] as const,
    detail: (id: string) => ['quotations', id] as const,
    lines: (id: string) => ['quotations', id, 'lines'] as const,
    risk: (id: string) => ['quotations', id, 'risk'] as const,
    approvals: (id: string) => ['quotations', id, 'approvals'] as const,
    recommendations: (id: string) => ['quotations', id, 'recommendations'] as const,
  },
  approvals: {
    all: ['approvals'] as const,
    pending: ['approvals', 'pending'] as const,
    detail: (id: string) => ['approvals', id] as const,
  },
  fulfillment: {
    order: (orderId: string) => ['orders', orderId, 'fulfillment'] as const,
    allocations: (orderId: string) => ['orders', orderId, 'fulfillment', 'allocations'] as const,
    backorders: ['backorders'] as const,
  },
  billing: {
    order: (orderId: string) => ['orders', orderId, 'billing'] as const,
    invoices: ['invoices'] as const,
    subscriptions: ['subscriptions'] as const,
    schedules: ['billing-schedules'] as const,
  },
  portal: {
    quotations: ['portal', 'quotations'] as const,
    detail: (id: string) => ['portal', 'quotations', id] as const,
    negotiations: (id: string) => ['portal', 'quotations', id, 'negotiations'] as const,
  },
  health: {
    dashboard: ['deal-health'] as const,
    alerts: ['deal-alerts'] as const,
  },
  reports: {
    summary: ['reports', 'summary'] as const,
    salesPerformance: (params: Record<string, any>) => ['reports', 'sales-performance', params] as const,
  },
  governance: {
    config: ['governance', 'config'] as const,
  }
};
