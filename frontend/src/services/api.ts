/**
 * DealFlow360 API Service Layer
 * 
 * Maps frontend models to the future FastAPI endpoint contract:
 * Base URL: /api/v1
 * 
 * In this frontend-only prototype, these services provide typed contract hooks
 * and query keys compatible with TanStack Query.
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const queryKeys = {
  auth: {
    me: ['auth', 'me'] as const,
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

export { authService, AuthError } from './authService';
export { userService, UserAdminError } from './userService';

