import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  queryKeys,
  userService,
  customerService,
  customerTierService,
  catalogService,
  quotationService,
  approvalService,
  orderService,
  pipelineService,
  fulfillmentService,
  billingService,
  invoiceService,
  paymentService,
  subscriptionService,
  subscriptionPlanService,
  billingScheduleService,
  warehouseService,
  pricingService,
  discountRuleService,
  approvalPolicyService,
} from '../services/api';
import {
  AdminCreateUserRequest,
  CustomerCreateRequest,
  CustomerUpdateRequest,
  CustomerTierCreateRequest,
  CustomerTierUpdateRequest,
  CategoryCreateRequest,
  CategoryUpdateRequest,
  ProductCreateRequest,
  ProductUpdateRequest,
  VariantCreateRequest,
  VariantUpdateRequest,
} from '../types';
import type { QuotationCreateRequest, QuotationUpdateRequest, QuotationLineCreateRequest, QuotationLineUpdateRequest } from '../services/quotationService';
import type { ApprovalActionRequest } from '../services/approvalService';
import type { OrderUpdateRequest } from '../services/orderService';
import type { FulfillmentOverrideRequest, AllocationUpdateRequest } from '../services/fulfillmentService';
import type { RecordPaymentRequest } from '../services/invoiceService';
import type { SubscriptionModifyRequest, SubscriptionCancelRequest, ProrationPreviewRequest, ProrationApplyRequest } from '../services/subscriptionService';
import type { SubscriptionPlanCreateRequest, SubscriptionPlanUpdateRequest } from '../services/subscriptionPlanService';
import type { CreditNoteRequest } from '../services/billingService';
import type { WarehouseCreateRequest, WarehouseUpdateRequest, WarehouseInventoryCreateRequest, InventoryUpdateRequest } from '../services/warehouseService';
import type { PriceListCreateRequest, PriceListUpdateRequest, PriceListItemCreateRequest, PriceListItemUpdateRequest, PriceResolveRequest } from '../services/pricingService';
import type { DiscountRuleCreateRequest, DiscountRuleUpdateRequest } from '../services/discountRuleService';
import type { ApprovalPolicyCreateRequest, ApprovalPolicyUpdateRequest } from '../services/approvalPolicyService';

// ==========================================
// 1. Users Queries & Mutations
// ==========================================

export function useUsersQuery(params?: { role?: string; is_active?: boolean; skip?: number; limit?: number }) {
  return useQuery({ queryKey: queryKeys.users.list(params), queryFn: () => userService.getUsers(params), staleTime: 1000 * 60 * 2 });
}
export function useUserDetailQuery(id: string) {
  return useQuery({ queryKey: queryKeys.users.detail(id), queryFn: () => userService.getUser(id), enabled: Boolean(id) });
}
export function useApproversQuery() {
  return useQuery({ queryKey: queryKeys.users.approvers, queryFn: () => userService.getApprovers(), staleTime: 1000 * 60 * 5 });
}
export function useCreateUserMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (p: AdminCreateUserRequest) => userService.createUser(p), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.users.all }) });
}
export function useAdminChangePasswordMutation() {
  return useMutation({ mutationFn: ({ userId, newPassword }: { userId: string; newPassword: string }) => userService.adminChangePassword(userId, newPassword) });
}

// ==========================================
// 2. Customers Queries & Mutations
// ==========================================

export function useCustomersQuery(params?: { search?: string; customer_tier_id?: string; is_active?: boolean; skip?: number; limit?: number }) {
  return useQuery({ queryKey: queryKeys.customers.list(params), queryFn: () => customerService.getCustomers(params), staleTime: 1000 * 60 * 2 });
}
export function useCustomerDetailQuery(id: string) {
  return useQuery({ queryKey: queryKeys.customers.detail(id), queryFn: () => customerService.getCustomer(id), enabled: Boolean(id) });
}
export function useCustomerQuotationsQuery(id: string) {
  return useQuery({ queryKey: queryKeys.customers.quotations(id), queryFn: () => customerService.getCustomerQuotations(id), enabled: Boolean(id) });
}
export function useCustomerOrdersQuery(id: string) {
  return useQuery({ queryKey: queryKeys.customers.orders(id), queryFn: () => customerService.getCustomerOrders(id), enabled: Boolean(id) });
}
export function useCustomerSubscriptionsQuery(id: string) {
  return useQuery({ queryKey: queryKeys.customers.subscriptions(id), queryFn: () => customerService.getCustomerSubscriptions(id), enabled: Boolean(id) });
}
export function useCreateCustomerMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (p: CustomerCreateRequest) => customerService.createCustomer(p), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.customers.all }) });
}
export function useUpdateCustomerMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload: CustomerUpdateRequest }) => customerService.updateCustomer(id, payload), onSuccess: (_, { id }) => { qc.invalidateQueries({ queryKey: queryKeys.customers.all }); qc.invalidateQueries({ queryKey: queryKeys.customers.detail(id) }); } });
}
export function useDeleteCustomerMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => customerService.deleteCustomer(id), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.customers.all }) });
}

// ==========================================
// 3. Customer Tiers Queries & Mutations
// ==========================================

export function useCustomerTiersQuery(params?: { is_active?: boolean; skip?: number; limit?: number }) {
  return useQuery({ queryKey: queryKeys.customerTiers.list(params), queryFn: () => customerTierService.getCustomerTiers(params), staleTime: 1000 * 60 * 5 });
}
export function useCustomerTierDetailQuery(id: string) {
  return useQuery({ queryKey: queryKeys.customerTiers.detail(id), queryFn: () => customerTierService.getCustomerTier(id), enabled: Boolean(id) });
}
export function useCreateCustomerTierMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (p: CustomerTierCreateRequest) => customerTierService.createCustomerTier(p), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.customerTiers.all }) });
}
export function useUpdateCustomerTierMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload: CustomerTierUpdateRequest }) => customerTierService.updateCustomerTier(id, payload), onSuccess: (_, { id }) => { qc.invalidateQueries({ queryKey: queryKeys.customerTiers.all }); qc.invalidateQueries({ queryKey: queryKeys.customerTiers.detail(id) }); } });
}
export function useDeleteCustomerTierMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => customerTierService.deleteCustomerTier(id), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.customerTiers.all }) });
}

// ==========================================
// 4. Product Categories Queries & Mutations
// ==========================================

export function useProductCategoriesQuery() {
  return useQuery({ queryKey: queryKeys.productCategories.all, queryFn: () => catalogService.getCategories(), retry: 1 });
}
export function useCreateProductCategoryMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (p: CategoryCreateRequest) => catalogService.createCategory(p), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.productCategories.all }) });
}
export function useUpdateProductCategoryMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload: CategoryUpdateRequest }) => catalogService.updateCategory(id, payload), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.productCategories.all }) });
}
export function useDeleteProductCategoryMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => catalogService.deleteCategory(id), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.productCategories.all }) });
}

// ==========================================
// 5. Products Queries & Mutations
// ==========================================

export function useProductsQuery(params?: { search?: string; category_id?: string; is_active?: boolean }) {
  return useQuery({ queryKey: queryKeys.products.list(params), queryFn: () => catalogService.getProducts(), retry: 1 });
}
export function useProductDetailQuery(id: string) {
  return useQuery({ queryKey: queryKeys.products.detail(id), queryFn: () => catalogService.getProduct(id), enabled: Boolean(id), retry: 1 });
}
export function useProductVariantsQuery(productId: string) {
  return useQuery({ queryKey: queryKeys.products.variants(productId), queryFn: () => catalogService.getProductVariants(productId), enabled: Boolean(productId), retry: 1 });
}
export function useCreateProductMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (p: ProductCreateRequest) => catalogService.createProduct(p), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.products.all }) });
}
export function useUpdateProductMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload: ProductUpdateRequest }) => catalogService.updateProduct(id, payload), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.products.all }) });
}
export function useDeleteProductMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => catalogService.deleteProduct(id), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.products.all }) });
}
export function useCreateVariantMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ productId, payload }: { productId: string; payload: VariantCreateRequest }) => catalogService.createVariant(productId, payload), onSuccess: (_, { productId }) => { qc.invalidateQueries({ queryKey: queryKeys.products.variants(productId) }); qc.invalidateQueries({ queryKey: queryKeys.variants.all }); } });
}
export function useUpdateVariantMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload: VariantUpdateRequest }) => catalogService.updateVariant(id, payload), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.variants.all }) });
}
export function useDeleteVariantMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => catalogService.deleteVariant(id), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.variants.all }) });
}

// ==========================================
// 6. Quotations Queries & Mutations
// ==========================================

export function useQuotationsQuery(params?: { status?: string; customer_id?: string; sales_rep_id?: string; skip?: number; limit?: number }) {
  return useQuery({ queryKey: queryKeys.quotations.list(params), queryFn: () => quotationService.listQuotations(params), staleTime: 1000 * 30 });
}
export function useQuotationDetailQuery(id: string) {
  return useQuery({ queryKey: queryKeys.quotations.detail(id), queryFn: () => quotationService.getQuotation(id), enabled: Boolean(id) });
}
export function useQuotationLinesQuery(id: string) {
  return useQuery({ queryKey: queryKeys.quotations.lines(id), queryFn: () => quotationService.getLines(id), enabled: Boolean(id) });
}
export function useQuotationRiskQuery(id: string) {
  return useQuery({ queryKey: queryKeys.quotations.risk(id), queryFn: () => quotationService.getRisk(id), enabled: Boolean(id) });
}
export function useQuotationApprovalsQuery(id: string) {
  return useQuery({ queryKey: queryKeys.quotations.approvals(id), queryFn: () => quotationService.getApprovals(id), enabled: Boolean(id) });
}
export function useQuotationAuditLogQuery(id: string) {
  return useQuery({ queryKey: queryKeys.quotations.auditLog(id), queryFn: () => quotationService.getAuditLog(id), enabled: Boolean(id) });
}
export function useCreateQuotationMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (p: QuotationCreateRequest) => quotationService.createQuotation(p), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.quotations.all }) });
}
export function useUpdateQuotationMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload: QuotationUpdateRequest }) => quotationService.updateQuotation(id, payload), onSuccess: (_, { id }) => { qc.invalidateQueries({ queryKey: queryKeys.quotations.all }); qc.invalidateQueries({ queryKey: queryKeys.quotations.detail(id) }); } });
}
export function useDeleteQuotationMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => quotationService.deleteQuotation(id), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.quotations.all }) });
}
export function useAddQuotationLineMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ quotationId, payload }: { quotationId: string; payload: QuotationLineCreateRequest }) => quotationService.addLine(quotationId, payload), onSuccess: (_, { quotationId }) => { qc.invalidateQueries({ queryKey: queryKeys.quotations.detail(quotationId) }); qc.invalidateQueries({ queryKey: queryKeys.quotations.lines(quotationId) }); qc.invalidateQueries({ queryKey: queryKeys.quotations.risk(quotationId) }); } });
}
export function useUpdateQuotationLineMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ quotationId, lineId, payload }: { quotationId: string; lineId: string; payload: QuotationLineUpdateRequest }) => quotationService.updateLine(quotationId, lineId, payload), onSuccess: (_, { quotationId }) => { qc.invalidateQueries({ queryKey: queryKeys.quotations.detail(quotationId) }); qc.invalidateQueries({ queryKey: queryKeys.quotations.lines(quotationId) }); qc.invalidateQueries({ queryKey: queryKeys.quotations.risk(quotationId) }); } });
}
export function useDeleteQuotationLineMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ quotationId, lineId }: { quotationId: string; lineId: string }) => quotationService.deleteLine(quotationId, lineId), onSuccess: (_, { quotationId }) => { qc.invalidateQueries({ queryKey: queryKeys.quotations.detail(quotationId) }); qc.invalidateQueries({ queryKey: queryKeys.quotations.lines(quotationId) }); qc.invalidateQueries({ queryKey: queryKeys.quotations.risk(quotationId) }); } });
}
export function useRecalculateQuotationMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => quotationService.recalculate(id), onSuccess: (_, id) => { qc.invalidateQueries({ queryKey: queryKeys.quotations.detail(id) }); qc.invalidateQueries({ queryKey: queryKeys.quotations.risk(id) }); } });
}
export function useSubmitQuotationMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => quotationService.submit(id), onSuccess: (_, id) => { qc.invalidateQueries({ queryKey: queryKeys.quotations.all }); qc.invalidateQueries({ queryKey: queryKeys.quotations.detail(id) }); qc.invalidateQueries({ queryKey: queryKeys.approvals.all }); } });
}
export function useSendQuotationMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => quotationService.send(id), onSuccess: (_, id) => { qc.invalidateQueries({ queryKey: queryKeys.quotations.all }); qc.invalidateQueries({ queryKey: queryKeys.quotations.detail(id) }); } });
}
export function useConfirmQuotationMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => quotationService.confirm(id), onSuccess: (_, id) => { qc.invalidateQueries({ queryKey: queryKeys.quotations.all }); qc.invalidateQueries({ queryKey: queryKeys.quotations.detail(id) }); qc.invalidateQueries({ queryKey: queryKeys.orders.all }); } });
}

// ==========================================
// 7. Approvals Queries & Mutations
// ==========================================

export function useApprovalsQuery(params?: { status?: string; quotation_id?: string; skip?: number; limit?: number }) {
  return useQuery({ queryKey: queryKeys.approvals.list(params), queryFn: () => approvalService.listApprovals(params), staleTime: 1000 * 30 });
}
export function usePendingApprovalsQuery() {
  return useQuery({ queryKey: queryKeys.approvals.pending, queryFn: () => approvalService.listPending(), staleTime: 1000 * 30 });
}
export function useApprovalDetailQuery(id: string) {
  return useQuery({ queryKey: queryKeys.approvals.detail(id), queryFn: () => approvalService.getApproval(id), enabled: Boolean(id) });
}
export function useApprovalAuditLogQuery(id: string) {
  return useQuery({ queryKey: queryKeys.approvals.auditLog(id), queryFn: () => approvalService.getAuditLog(id), enabled: Boolean(id) });
}
export function useApproveStepMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload?: ApprovalActionRequest }) => approvalService.approve(id, payload), onSuccess: (_, { id }) => { qc.invalidateQueries({ queryKey: queryKeys.approvals.all }); qc.invalidateQueries({ queryKey: queryKeys.approvals.detail(id) }); qc.invalidateQueries({ queryKey: queryKeys.quotations.all }); } });
}
export function useRejectApprovalMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload?: ApprovalActionRequest }) => approvalService.reject(id, payload), onSuccess: (_, { id }) => { qc.invalidateQueries({ queryKey: queryKeys.approvals.all }); qc.invalidateQueries({ queryKey: queryKeys.approvals.detail(id) }); qc.invalidateQueries({ queryKey: queryKeys.quotations.all }); } });
}
export function useReturnForRevisionMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload?: ApprovalActionRequest }) => approvalService.returnForRevision(id, payload), onSuccess: (_, { id }) => { qc.invalidateQueries({ queryKey: queryKeys.approvals.all }); qc.invalidateQueries({ queryKey: queryKeys.approvals.detail(id) }); qc.invalidateQueries({ queryKey: queryKeys.quotations.all }); } });
}

// ==========================================
// 8. Orders Queries & Mutations
// ==========================================

export function useOrdersQuery(params?: { customer_id?: string; status?: string; skip?: number; limit?: number }) {
  return useQuery({ queryKey: queryKeys.orders.list(params), queryFn: () => orderService.listOrders(params), staleTime: 1000 * 60 });
}
export function useOrderDetailQuery(id: string) {
  return useQuery({ queryKey: queryKeys.orders.detail(id), queryFn: () => orderService.getOrder(id), enabled: Boolean(id) });
}
export function useOrderAuditLogQuery(id: string) {
  return useQuery({ queryKey: queryKeys.orders.auditLog(id), queryFn: () => orderService.getAuditLog(id), enabled: Boolean(id) });
}
export function useUpdateOrderMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload: OrderUpdateRequest }) => orderService.updateOrder(id, payload), onSuccess: (_, { id }) => { qc.invalidateQueries({ queryKey: queryKeys.orders.all }); qc.invalidateQueries({ queryKey: queryKeys.orders.detail(id) }); } });
}

// ==========================================
// 9. Pipeline
// ==========================================

export function usePipelineQuery() {
  return useQuery({ queryKey: queryKeys.pipeline.data, queryFn: () => pipelineService.getPipeline(), staleTime: 1000 * 30 });
}

// ==========================================
// 10. Fulfillment Queries & Mutations
// ==========================================

export function useFulfillmentQuery(orderId: string) {
  return useQuery({ queryKey: queryKeys.fulfillment.order(orderId), queryFn: () => fulfillmentService.getFulfillment(orderId), enabled: Boolean(orderId) });
}
export function useFulfillmentAllocationsQuery(orderId: string) {
  return useQuery({ queryKey: queryKeys.fulfillment.allocations(orderId), queryFn: () => fulfillmentService.getAllocations(orderId), enabled: Boolean(orderId) });
}
export function useOrderBackordersQuery(orderId: string) {
  return useQuery({ queryKey: queryKeys.fulfillment.backorders(orderId), queryFn: () => fulfillmentService.getOrderBackorders(orderId), enabled: Boolean(orderId) });
}
export function useBackordersQuery(params?: { status?: string; order_id?: string; skip?: number; limit?: number }) {
  return useQuery({ queryKey: queryKeys.backorders.list(params), queryFn: () => fulfillmentService.listBackorders(params), staleTime: 1000 * 60 });
}
export function useSuggestFulfillmentMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (orderId: string) => fulfillmentService.suggestFulfillment(orderId), onSuccess: (_, orderId) => qc.invalidateQueries({ queryKey: queryKeys.fulfillment.order(orderId) }) });
}
export function useAcceptFulfillmentMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (orderId: string) => fulfillmentService.acceptFulfillment(orderId), onSuccess: (_, orderId) => { qc.invalidateQueries({ queryKey: queryKeys.fulfillment.order(orderId) }); qc.invalidateQueries({ queryKey: queryKeys.orders.detail(orderId) }); } });
}
export function useOverrideFulfillmentMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ orderId, payload }: { orderId: string; payload: FulfillmentOverrideRequest }) => fulfillmentService.overrideFulfillment(orderId, payload), onSuccess: (_, { orderId }) => { qc.invalidateQueries({ queryKey: queryKeys.fulfillment.order(orderId) }); qc.invalidateQueries({ queryKey: queryKeys.fulfillment.allocations(orderId) }); } });
}
export function useCompleteFulfillmentMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (orderId: string) => fulfillmentService.completeFulfillment(orderId), onSuccess: (_, orderId) => { qc.invalidateQueries({ queryKey: queryKeys.fulfillment.order(orderId) }); qc.invalidateQueries({ queryKey: queryKeys.orders.detail(orderId) }); } });
}
export function useConsolidateBackorderMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => fulfillmentService.consolidateBackorder(id), onSuccess: () => { qc.invalidateQueries({ queryKey: queryKeys.backorders.all }); qc.invalidateQueries({ queryKey: queryKeys.orders.all }); } });
}
export function useCancelBackorderMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => fulfillmentService.cancelBackorder(id), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.backorders.all }) });
}

// ==========================================
// 11. Billing (Order-level)
// ==========================================

export function useOrderBillingQuery(orderId: string) {
  return useQuery({ queryKey: queryKeys.billing.order(orderId), queryFn: () => billingService.getOrderBilling(orderId), enabled: Boolean(orderId) });
}
export function useGenerateBillingMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (orderId: string) => billingService.generateBilling(orderId), onSuccess: (_, orderId) => { qc.invalidateQueries({ queryKey: queryKeys.billing.order(orderId) }); qc.invalidateQueries({ queryKey: queryKeys.invoices.all }); qc.invalidateQueries({ queryKey: queryKeys.subscriptions.all }); } });
}
export function useCreateCreditNoteMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ orderId, payload }: { orderId: string; payload: CreditNoteRequest }) => billingService.createCreditNote(orderId, payload), onSuccess: (_, { orderId }) => { qc.invalidateQueries({ queryKey: queryKeys.billing.order(orderId) }); qc.invalidateQueries({ queryKey: queryKeys.invoices.all }); } });
}

// ==========================================
// 12. Invoices Queries & Mutations
// ==========================================

export function useInvoicesQuery(params?: { order_id?: string; status?: string; invoice_type?: string; skip?: number; limit?: number }) {
  return useQuery({ queryKey: queryKeys.invoices.list(params), queryFn: () => invoiceService.listInvoices(params), staleTime: 1000 * 60 });
}
export function useInvoiceDetailQuery(id: string) {
  return useQuery({ queryKey: queryKeys.invoices.detail(id), queryFn: () => invoiceService.getInvoice(id), enabled: Boolean(id) });
}
export function useInvoicePaymentsQuery(id: string) {
  return useQuery({ queryKey: queryKeys.invoices.payments(id), queryFn: () => invoiceService.getPayments(id), enabled: Boolean(id) });
}
export function useIssueInvoiceMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => invoiceService.issueInvoice(id), onSuccess: (_, id) => { qc.invalidateQueries({ queryKey: queryKeys.invoices.all }); qc.invalidateQueries({ queryKey: queryKeys.invoices.detail(id) }); } });
}
export function useCancelInvoiceMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => invoiceService.cancelInvoice(id), onSuccess: (_, id) => { qc.invalidateQueries({ queryKey: queryKeys.invoices.all }); qc.invalidateQueries({ queryKey: queryKeys.invoices.detail(id) }); } });
}
export function useRecordPaymentMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ invoiceId, payload }: { invoiceId: string; payload: RecordPaymentRequest }) => invoiceService.recordPayment(invoiceId, payload), onSuccess: (_, { invoiceId }) => { qc.invalidateQueries({ queryKey: queryKeys.invoices.all }); qc.invalidateQueries({ queryKey: queryKeys.invoices.detail(invoiceId) }); qc.invalidateQueries({ queryKey: queryKeys.invoices.payments(invoiceId) }); qc.invalidateQueries({ queryKey: queryKeys.payments.all }); } });
}

// ==========================================
// 13. Payments Queries & Mutations
// ==========================================

export function usePaymentsQuery(params?: { invoice_id?: string; status?: string; skip?: number; limit?: number }) {
  return useQuery({ queryKey: queryKeys.payments.list(params), queryFn: () => paymentService.listPayments(params), staleTime: 1000 * 60 });
}
export function usePaymentDetailQuery(id: string) {
  return useQuery({ queryKey: queryKeys.payments.detail(id), queryFn: () => paymentService.getPayment(id), enabled: Boolean(id) });
}
export function useRefundPaymentMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => paymentService.refundPayment(id), onSuccess: () => { qc.invalidateQueries({ queryKey: queryKeys.payments.all }); qc.invalidateQueries({ queryKey: queryKeys.invoices.all }); } });
}

// ==========================================
// 14. Subscriptions Queries & Mutations
// ==========================================

export function useSubscriptionsQuery(params?: { customer_id?: string; status?: string; order_id?: string; skip?: number; limit?: number }) {
  return useQuery({ queryKey: queryKeys.subscriptions.list(params), queryFn: () => subscriptionService.listSubscriptions(params), staleTime: 1000 * 60 });
}
export function useSubscriptionDetailQuery(id: string) {
  return useQuery({ queryKey: queryKeys.subscriptions.detail(id), queryFn: () => subscriptionService.getSubscription(id), enabled: Boolean(id) });
}
export function useModifySubscriptionMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload: SubscriptionModifyRequest }) => subscriptionService.modifySubscription(id, payload), onSuccess: () => { qc.invalidateQueries({ queryKey: queryKeys.subscriptions.all }); } });
}
export function useCancelSubscriptionMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload?: SubscriptionCancelRequest }) => subscriptionService.cancelSubscription(id, payload), onSuccess: () => { qc.invalidateQueries({ queryKey: queryKeys.subscriptions.all }); } });
}
export function usePauseSubscriptionMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => subscriptionService.pauseSubscription(id), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.subscriptions.all }) });
}
export function useProrationPreviewMutation() {
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload: ProrationPreviewRequest }) => subscriptionService.previewProration(id, payload) });
}
export function useProrationApplyMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload: ProrationApplyRequest }) => subscriptionService.applyProration(id, payload), onSuccess: () => { qc.invalidateQueries({ queryKey: queryKeys.subscriptions.all }); qc.invalidateQueries({ queryKey: queryKeys.invoices.all }); } });
}

// ==========================================
// 15. Subscription Plans Queries & Mutations
// ==========================================

export function useSubscriptionPlansQuery(params?: { is_active?: boolean; skip?: number; limit?: number }) {
  return useQuery({ queryKey: queryKeys.subscriptionPlans.list(params), queryFn: () => subscriptionPlanService.listPlans(params), staleTime: 1000 * 60 * 5 });
}
export function useCreateSubscriptionPlanMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (p: SubscriptionPlanCreateRequest) => subscriptionPlanService.createPlan(p), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.subscriptionPlans.all }) });
}
export function useUpdateSubscriptionPlanMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload: SubscriptionPlanUpdateRequest }) => subscriptionPlanService.updatePlan(id, payload), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.subscriptionPlans.all }) });
}
export function useDeleteSubscriptionPlanMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => subscriptionPlanService.deletePlan(id), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.subscriptionPlans.all }) });
}

// ==========================================
// 16. Billing Schedules Queries & Mutations
// ==========================================

export function useBillingSchedulesQuery(params?: { subscription_id?: string; status?: string; skip?: number; limit?: number }) {
  return useQuery({ queryKey: queryKeys.billingSchedules.list(params), queryFn: () => billingScheduleService.listSchedules(params), staleTime: 1000 * 60 });
}
export function useGenerateScheduleInvoiceMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => billingScheduleService.generateInvoice(id), onSuccess: () => { qc.invalidateQueries({ queryKey: queryKeys.billingSchedules.all }); qc.invalidateQueries({ queryKey: queryKeys.invoices.all }); } });
}
export function useCancelBillingScheduleMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => billingScheduleService.cancelSchedule(id), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.billingSchedules.all }) });
}

// ==========================================
// 17. Warehouses & Inventory Queries & Mutations
// ==========================================

export function useWarehousesQuery(params?: { is_active?: boolean; skip?: number; limit?: number }) {
  return useQuery({ queryKey: queryKeys.warehouses.list(params), queryFn: () => warehouseService.listWarehouses(params), staleTime: 1000 * 60 * 5 });
}
export function useWarehouseDetailQuery(id: string) {
  return useQuery({ queryKey: queryKeys.warehouses.detail(id), queryFn: () => warehouseService.getWarehouse(id), enabled: Boolean(id) });
}
export function useWarehouseInventoryQuery(warehouseId: string) {
  return useQuery({ queryKey: queryKeys.warehouses.inventory(warehouseId), queryFn: () => warehouseService.getWarehouseInventory(warehouseId), enabled: Boolean(warehouseId) });
}
export function useCreateWarehouseMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (p: WarehouseCreateRequest) => warehouseService.createWarehouse(p), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.warehouses.all }) });
}
export function useUpdateWarehouseMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload: WarehouseUpdateRequest }) => warehouseService.updateWarehouse(id, payload), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.warehouses.all }) });
}
export function useDeleteWarehouseMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => warehouseService.deleteWarehouse(id), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.warehouses.all }) });
}
export function useConfigureInventoryMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ warehouseId, payload }: { warehouseId: string; payload: WarehouseInventoryCreateRequest }) => warehouseService.configureInventory(warehouseId, payload), onSuccess: (_, { warehouseId }) => { qc.invalidateQueries({ queryKey: queryKeys.warehouses.inventory(warehouseId) }); qc.invalidateQueries({ queryKey: queryKeys.inventory.all }); } });
}
export function useInventoryQuery(params?: { warehouse_id?: string; product_id?: string; skip?: number; limit?: number }) {
  return useQuery({ queryKey: queryKeys.inventory.list(params), queryFn: () => warehouseService.listInventory(params), staleTime: 1000 * 60 });
}
export function useUpdateInventoryMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload: InventoryUpdateRequest }) => warehouseService.updateInventory(id, payload), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.inventory.all }) });
}
export function useProductInventoryQuery(productId: string) {
  return useQuery({ queryKey: queryKeys.inventory.product(productId), queryFn: () => warehouseService.getProductInventory(productId), enabled: Boolean(productId) });
}

// ==========================================
// 18. Pricing (Price Lists) Queries & Mutations
// ==========================================

export function usePriceListsQuery(params?: { customer_tier_id?: string; currency?: string; is_active?: boolean; skip?: number; limit?: number }) {
  return useQuery({ queryKey: queryKeys.priceLists.list(params), queryFn: () => pricingService.listPriceLists(params), staleTime: 1000 * 60 * 5 });
}
export function usePriceListItemsQuery(priceListId: string) {
  return useQuery({ queryKey: queryKeys.priceLists.items(priceListId), queryFn: () => pricingService.listItems(priceListId), enabled: Boolean(priceListId) });
}
export function useCreatePriceListMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (p: PriceListCreateRequest) => pricingService.createPriceList(p), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.priceLists.all }) });
}
export function useUpdatePriceListMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload: PriceListUpdateRequest }) => pricingService.updatePriceList(id, payload), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.priceLists.all }) });
}
export function useDeletePriceListMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => pricingService.deletePriceList(id), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.priceLists.all }) });
}
export function useAddPriceListItemMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ priceListId, payload }: { priceListId: string; payload: PriceListItemCreateRequest }) => pricingService.addItem(priceListId, payload), onSuccess: (_, { priceListId }) => qc.invalidateQueries({ queryKey: queryKeys.priceLists.items(priceListId) }) });
}
export function useUpdatePriceListItemMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ priceListId, itemId, payload }: { priceListId: string; itemId: string; payload: PriceListItemUpdateRequest }) => pricingService.updateItem(priceListId, itemId, payload), onSuccess: (_, { priceListId }) => qc.invalidateQueries({ queryKey: queryKeys.priceLists.items(priceListId) }) });
}
export function useDeletePriceListItemMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ priceListId, itemId }: { priceListId: string; itemId: string }) => pricingService.deleteItem(priceListId, itemId), onSuccess: (_, { priceListId }) => qc.invalidateQueries({ queryKey: queryKeys.priceLists.items(priceListId) }) });
}
export function useResolvePriceMutation() {
  return useMutation({ mutationFn: (payload: PriceResolveRequest) => pricingService.resolvePrice(payload) });
}

// ==========================================
// 19. Discount Rules Queries & Mutations
// ==========================================

export function useDiscountRulesQuery(params?: { customer_tier_id?: string; category_id?: string; is_active?: boolean; skip?: number; limit?: number }) {
  return useQuery({ queryKey: queryKeys.discountRules.list(params), queryFn: () => discountRuleService.listRules(params), staleTime: 1000 * 60 * 5 });
}
export function useCreateDiscountRuleMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (p: DiscountRuleCreateRequest) => discountRuleService.createRule(p), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.discountRules.all }) });
}
export function useUpdateDiscountRuleMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload: DiscountRuleUpdateRequest }) => discountRuleService.updateRule(id, payload), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.discountRules.all }) });
}
export function useDeleteDiscountRuleMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => discountRuleService.deleteRule(id), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.discountRules.all }) });
}

// ==========================================
// 20. Approval Policies Queries & Mutations
// ==========================================

export function useApprovalPoliciesQuery(params?: { is_active?: boolean; skip?: number; limit?: number }) {
  return useQuery({ queryKey: queryKeys.approvalPolicies.list(params), queryFn: () => approvalPolicyService.listPolicies(params), staleTime: 1000 * 60 * 5 });
}
export function useCreateApprovalPolicyMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (p: ApprovalPolicyCreateRequest) => approvalPolicyService.createPolicy(p), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.approvalPolicies.all }) });
}
export function useUpdateApprovalPolicyMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ id, payload }: { id: string; payload: ApprovalPolicyUpdateRequest }) => approvalPolicyService.updatePolicy(id, payload), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.approvalPolicies.all }) });
}
export function useDeleteApprovalPolicyMutation() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (id: string) => approvalPolicyService.deletePolicy(id), onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.approvalPolicies.all }) });
}
