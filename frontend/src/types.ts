export type UserRole =
  | 'SALES_REP'
  | 'SALES_MANAGER'
  | 'FINANCE_OPERATIONS'
  | 'FULFILLMENT_OPERATOR'
  | 'CUSTOMER_PORTAL'
  | 'CUSTOMER'
  | 'ADMIN';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar: string;
  title: string;
  department: string;
  customerId?: string; // For customer portal users
}

export type CustomerTier = 'BRONZE' | 'SILVER' | 'GOLD' | 'PLATINUM';

export interface Customer {
  id: string;
  name: string;
  companyNumber: string;
  tier: CustomerTier;
  industry: string;
  contactName: string;
  contactEmail: string;
  defaultDiscountCeiling: number; // e.g. Gold = 15%
  balance: number;
}

export type ProductCategory = 'HARDWARE' | 'SERVICES' | 'SUBSCRIPTION';

export interface Product {
  id: string;
  name: string;
  sku: string;
  category: ProductCategory;
  unitPrice: number;
  unitCost: number;
  unit: string;
  taxRate: number; // e.g. 0.08 for 8%
  description: string;
  isSubscriptionEligible: boolean;
  recurringInterval?: 'MONTHLY' | 'QUARTERLY' | 'YEARLY';
  categoryDiscountCeiling: number; // Category specific discount ceiling %
}

export interface QuotationLine {
  id: string;
  productId: string;
  productName: string;
  category: ProductCategory;
  quantity: number;
  unitPrice: number;
  unitCost: number;
  discountPercent: number;
  allowedDiscountCeiling: number;
  discountExcessPercent: number; // How much it exceeds ceiling
  lineTotal: number;
  marginPercent: number;
  isSubscription: boolean;
  recurringInterval?: 'MONTHLY' | 'QUARTERLY' | 'YEARLY';
  comments?: string[];
}

export type QuotationStage =
  | 'DRAFT'
  | 'PENDING_APPROVAL'
  | 'UNDER_REVIEW'
  | 'APPROVED'
  | 'REJECTED'
  | 'RETURNED_FOR_REVISION'
  | 'SENT'
  | 'NEGOTIATION'
  | 'UNDER_NEGOTIATION'
  | 'CONFIRMED';

export type ApprovalLevel = 'NONE' | 'SALES_MANAGER' | 'MANAGER_AND_FINANCE';

export interface Recommendation {
  productId: string;
  productName: string;
  category: ProductCategory;
  unitPrice: number;
  marginDelta: number; // e.g. +4.2%
  promotionTag?: string; // e.g. "Special Bundle", "Q3 Promo"
  reason: string;
}

export interface Quotation {
  id: string;
  quoteNumber: string;
  customerId: string;
  customerName: string;
  customerTier: CustomerTier;
  salesRepId: string;
  salesRepName: string;
  createdAt: string;
  updatedAt: string;
  stage: QuotationStage;
  lines: QuotationLine[];
  orderDiscountPercent: number;
  subtotal: number;
  totalDiscountAmount: number;
  taxAmount: number;
  totalAmount: number;
  totalCost: number;
  blendedMarginPercent: number;
  blendedRiskScore: number; // 0-100
  riskStatus: 'HEALTHY' | 'MODERATE' | 'HIGH_RISK';
  riskReasons: string[];
  approvalRequired: boolean;
  requiredApprovalLevel: ApprovalLevel;
  currentApprovalStep?: 'MANAGER' | 'FINANCE' | 'COMPLETED';
  hasActiveNegotiation?: boolean;
}

export interface ApprovalStep {
  id: string;
  stepNumber: number;
  roleRequired: 'SALES_MANAGER' | 'FINANCE_OPERATIONS';
  reviewerName?: string;
  reviewerId?: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'REVISION_REQUESTED';
  comment?: string;
  decidedAt?: string;
}

export interface ApprovalInstance {
  id: string;
  quotationId: string;
  quoteNumber: string;
  customerName: string;
  salesRepName?: string;
  amount: number;
  riskScore: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'REVISION_REQUIRED';
  steps: ApprovalStep[];
  submittedAt: string;
  reasons: string[];
  reason?: string;
  auditTimeline: AuditLog[];
}

export interface AuditLog {
  id: string;
  entityType: 'QUOTATION' | 'APPROVAL' | 'FULFILLMENT' | 'BILLING' | 'NEGOTIATION';
  entityId: string;
  userName: string;
  userRole: string;
  action: string;
  timestamp: string;
  reason?: string;
  details?: string;
}

export interface Warehouse {
  id: string;
  name: string;
  code: string;
  city: string;
  shippingWeight: number; // Cost factor weighting
  stockByProduct: Record<string, number>; // productId -> available qty
}

export interface FulfillmentAllocation {
  warehouseId: string;
  warehouseName: string;
  productId: string;
  productName: string;
  quantityAllocated: number;
  estimatedShipments: number;
  estimatedCost: number;
}

export interface OrderFulfillment {
  orderId: string;
  quotationId: string;
  quoteNumber: string;
  customerName: string;
  status: 'PENDING' | 'SUGGESTED' | 'ACCEPTED' | 'MANUALLY_OVERRIDDEN' | 'PARTIALLY_FULFILLED' | 'BACKORDERED' | 'FULFILLED';
  allocations: FulfillmentAllocation[];
  totalShipments: number;
  totalShippingCost: number;
  backorderQuantity: number;
  backorderProductNames: string[];
  consolidationAvailable?: boolean;
}

export interface SubscriptionItem {
  id: string;
  orderId: string;
  productName: string;
  quantity: number;
  amount: number;
  interval: 'MONTHLY' | 'QUARTERLY' | 'YEARLY';
  startDate: string;
  nextBillingDate: string;
  status: 'ACTIVE' | 'PAUSED' | 'CANCELLED';
  prorationApplied?: number;
}

export interface Invoice {
  id: string;
  invoiceNumber: string;
  orderId: string;
  customerName: string;
  type: 'ONE_TIME' | 'RECURRING' | 'CREDIT_NOTE';
  amount: number;
  paidAmount: number;
  status: 'DRAFT' | 'ISSUED' | 'PARTIALLY_PAID' | 'PAID' | 'CANCELLED';
  dueDate: string;
  issuedAt: string;
}

export interface DealAlert {
  id: string;
  quotationId: string;
  quoteNumber: string;
  customerName: string;
  ownerName: string;
  type: 'STALLED' | 'DISCOUNT_ANOMALY' | 'DELIVERY_SLIPPAGE';
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  reason: string;
  ageDays: number;
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED';
  suggestedAction: string;
}

export interface NegotiationRequest {
  id: string;
  quotationId: string;
  customerName: string;
  requestedDiscountPercent: number;
  notes: string;
  status: 'PENDING_REVIEW' | 'ACCEPTED' | 'COUNTERED' | 'REJECTED';
  createdAt: string;
  lineComments: { lineId: string; comment: string; productName?: string }[];
  repResponseNotes?: string;
  counterDiscountPercent?: number;
  respondedAt?: string;
}

export interface GovernanceConfig {
  roleCeilings: {
    repCeiling: number;
    managerCeiling: number;
    financeCeiling: number;
  };
  tierDiscountCeilings: Record<CustomerTier, number>;
  categoryDiscountCeilings: Record<ProductCategory, number>;
  managerApprovalRiskThreshold: number;
  financeApprovalRiskThreshold: number;
  minCorporateMarginFloor: number;
  riskWeights: {
    discountBreach: number;
    marginDeviation: number;
    paymentRisk: number;
  };
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthUserInfo {
  id: string;
  email: string;
  name?: string;
  role?: UserRole | string;
  is_active?: boolean;
  customerId?: string;
  customer_id?: string | null;
  title?: string;
  department?: string;
  avatar?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type?: string;
  expires_in?: number;
  user?: AuthUserInfo;
}

export interface RefreshResponse {
  access_token: string;
  token_type?: string;
  expires_in?: number;
}

export interface LogoutResponse {
  message?: string;
  success?: boolean;
}

export interface SignupRequest {
  name: string;
  email: string;
  password: string;
}

export interface UserResponse {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  customer_id?: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AdminCreateUserRequest {
  name: string;
  email: string;
  password: string;
  role: 'CUSTOMER' | 'SALES_REP' | 'SALES_MANAGER' | 'FINANCE_OPERATIONS' | 'ADMIN';
  customer_id?: string;
  is_active?: boolean;
}

export interface MessageResponse {
  message: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface AdminChangePasswordRequest {
  new_password: string;
}

// Backend Customer Contracts (Matches /api/v1/customers schemas)
export interface CustomerResponse {
  id: string;
  name: string;
  email?: string | null;
  phone?: string | null;
  customer_tier_id: string;
  billing_address?: string | null;
  shipping_address?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CustomerDetailResponse extends CustomerResponse {
  customer_tier?: CustomerTierResponse | null;
}

export interface CustomerCreateRequest {
  name: string;
  customer_tier_id: string;
  email?: string | null;
  phone?: string | null;
  billing_address?: string | null;
  shipping_address?: string | null;
  is_active?: boolean;
}

export interface CustomerUpdateRequest {
  name?: string | null;
  customer_tier_id?: string | null;
  email?: string | null;
  phone?: string | null;
  billing_address?: string | null;
  shipping_address?: string | null;
  is_active?: boolean | null;
}

// Backend Customer Tier Contracts (Matches /api/v1/customer-tiers schemas)
export interface CustomerTierResponse {
  id: string;
  name: string;
  description?: string | null;
  default_discount_limit: string | number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CustomerTierCreateRequest {
  name: string;
  default_discount_limit: number | string;
  description?: string | null;
  is_active?: boolean;
}

export interface CustomerTierUpdateRequest {
  name?: string | null;
  default_discount_limit?: number | string | null;
  description?: string | null;
  is_active?: boolean | null;
}

// Backend Customer History Summaries
export interface BackendQuotationSummary {
  id: string;
  quotation_number: string;
  customer_id: string;
  sales_rep_id: string;
  status: string;
  subtotal: string | number;
  discount_amount: string | number;
  order_discount_percent: string | number;
  tax_amount: string | number;
  total_amount: string | number;
  total_cost: string | number;
  margin_amount: string | number;
  margin_percent: string | number;
  risk_score: string | number;
  approval_required: boolean;
  last_activity_at: string;
  valid_until?: string | null;
  created_at: string;
  updated_at: string;
}

export interface BackendOrderSummary {
  id: string;
  order_number: string;
  customer_id: string;
  quotation_id: string;
  status: string;
  total_amount: string | number;
  created_at: string;
  updated_at: string;
}

export interface BackendSubscriptionSummary {
  id: string;
  order_id: string;
  quotation_line_id: string;
  customer_id: string;
  product_id: string;
  plan_id: string;
  quantity: string | number;
  unit_price: string | number;
  start_date: string;
  next_billing_date: string;
  status: string;
  created_at: string;
  updated_at: string;
}

// Product Category Contracts (Matches /api/v1/product-categories contract)
export interface CategoryResponse {
  id: string;
  name: string;
  code?: string;
  description?: string | null;
  max_discount_ceiling?: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface CategoryCreateRequest {
  name: string;
  code?: string;
  description?: string | null;
  max_discount_ceiling?: number;
  is_active?: boolean;
}

export interface CategoryUpdateRequest {
  name?: string;
  code?: string;
  description?: string | null;
  max_discount_ceiling?: number;
  is_active?: boolean;
}

// Product & Variant Contracts (Matches /api/v1/products and /api/v1/variants contracts)
export interface ProductItemResponse {
  id: string;
  name: string;
  sku: string;
  category_id?: string;
  category?: ProductCategory | string;
  unit_price: number | string;
  unit_cost: number | string;
  tax_rate?: number | string;
  is_subscription_eligible?: boolean;
  description?: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ProductCreateRequest {
  name: string;
  sku: string;
  category_id?: string;
  unit_price: number;
  unit_cost: number;
  description?: string;
  is_subscription_eligible?: boolean;
  is_active?: boolean;
}

export interface ProductUpdateRequest {
  name?: string;
  sku?: string;
  category_id?: string;
  unit_price?: number;
  unit_cost?: number;
  description?: string;
  is_subscription_eligible?: boolean;
  is_active?: boolean;
}

export interface VariantResponse {
  id: string;
  product_id: string;
  name: string;
  sku: string;
  price_adjustment?: number | string;
  cost_adjustment?: number | string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface VariantCreateRequest {
  name: string;
  sku: string;
  price_adjustment?: number;
  cost_adjustment?: number;
  is_active?: boolean;
}

export interface VariantUpdateRequest {
  name?: string;
  sku?: string;
  price_adjustment?: number;
  cost_adjustment?: number;
  is_active?: boolean;
}


