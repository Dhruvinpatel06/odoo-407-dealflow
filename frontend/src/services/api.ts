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
export { quotationService } from './quotationService';
export { approvalService } from './approvalService';
export { orderService } from './orderService';
export { pipelineService } from './pipelineService';
export { fulfillmentService } from './fulfillmentService';
export { billingService } from './billingService';
export { invoiceService } from './invoiceService';
export { paymentService } from './paymentService';
export { subscriptionService } from './subscriptionService';
export { subscriptionPlanService } from './subscriptionPlanService';
export { billingScheduleService } from './billingScheduleService';
export { warehouseService } from './warehouseService';
export { pricingService } from './pricingService';
export { discountRuleService } from './discountRuleService';
export { approvalPolicyService } from './approvalPolicyService';

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
    list: (params?: Record<string, any>) => ['quotations', 'list', params] as const,
    detail: (id: string) => ['quotations', id] as const,
    lines: (id: string) => ['quotations', id, 'lines'] as const,
    risk: (id: string) => ['quotations', id, 'risk'] as const,
    approvals: (id: string) => ['quotations', id, 'approvals'] as const,
    auditLog: (id: string) => ['quotations', id, 'audit-log'] as const,
  },
  approvals: {
    all: ['approvals'] as const,
    list: (params?: Record<string, any>) => ['approvals', 'list', params] as const,
    pending: ['approvals', 'pending'] as const,
    detail: (id: string) => ['approvals', id] as const,
    auditLog: (id: string) => ['approvals', id, 'audit-log'] as const,
  },
  orders: {
    all: ['orders'] as const,
    list: (params?: Record<string, any>) => ['orders', 'list', params] as const,
    detail: (id: string) => ['orders', id] as const,
    auditLog: (id: string) => ['orders', id, 'audit-log'] as const,
  },
  pipeline: {
    data: ['pipeline'] as const,
  },
  fulfillment: {
    order: (orderId: string) => ['orders', orderId, 'fulfillment'] as const,
    allocations: (orderId: string) => ['orders', orderId, 'fulfillment', 'allocations'] as const,
    backorders: (orderId: string) => ['orders', orderId, 'backorders'] as const,
  },
  backorders: {
    all: ['backorders'] as const,
    list: (params?: Record<string, any>) => ['backorders', 'list', params] as const,
    detail: (id: string) => ['backorders', id] as const,
  },
  billing: {
    order: (orderId: string) => ['orders', orderId, 'billing'] as const,
  },
  invoices: {
    all: ['invoices'] as const,
    list: (params?: Record<string, any>) => ['invoices', 'list', params] as const,
    detail: (id: string) => ['invoices', id] as const,
    payments: (id: string) => ['invoices', id, 'payments'] as const,
    creditNotes: (id: string) => ['invoices', id, 'credit-notes'] as const,
  },
  payments: {
    all: ['payments'] as const,
    list: (params?: Record<string, any>) => ['payments', 'list', params] as const,
    detail: (id: string) => ['payments', id] as const,
  },
  subscriptions: {
    all: ['subscriptions'] as const,
    list: (params?: Record<string, any>) => ['subscriptions', 'list', params] as const,
    detail: (id: string) => ['subscriptions', id] as const,
  },
  subscriptionPlans: {
    all: ['subscription-plans'] as const,
    list: (params?: Record<string, any>) => ['subscription-plans', 'list', params] as const,
    detail: (id: string) => ['subscription-plans', id] as const,
  },
  billingSchedules: {
    all: ['billing-schedules'] as const,
    list: (params?: Record<string, any>) => ['billing-schedules', 'list', params] as const,
    detail: (id: string) => ['billing-schedules', id] as const,
  },
  warehouses: {
    all: ['warehouses'] as const,
    list: (params?: Record<string, any>) => ['warehouses', 'list', params] as const,
    detail: (id: string) => ['warehouses', id] as const,
    inventory: (id: string) => ['warehouses', id, 'inventory'] as const,
  },
  inventory: {
    all: ['inventory'] as const,
    list: (params?: Record<string, any>) => ['inventory', 'list', params] as const,
    detail: (id: string) => ['inventory', id] as const,
    product: (productId: string) => ['inventory', 'product', productId] as const,
  },
  priceLists: {
    all: ['price-lists'] as const,
    list: (params?: Record<string, any>) => ['price-lists', 'list', params] as const,
    detail: (id: string) => ['price-lists', id] as const,
    items: (id: string) => ['price-lists', id, 'items'] as const,
  },
  discountRules: {
    all: ['discount-rules'] as const,
    list: (params?: Record<string, any>) => ['discount-rules', 'list', params] as const,
    detail: (id: string) => ['discount-rules', id] as const,
  },
  approvalPolicies: {
    all: ['approval-policies'] as const,
    list: (params?: Record<string, any>) => ['approval-policies', 'list', params] as const,
    detail: (id: string) => ['approval-policies', id] as const,
  },
};
