import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  queryKeys,
  userService,
  customerService,
  customerTierService,
  catalogService
} from '../services/api';
import {
  AdminCreateUserRequest,
  UserResponse,
  CustomerCreateRequest,
  CustomerUpdateRequest,
  CustomerTierCreateRequest,
  CustomerTierUpdateRequest,
  CategoryCreateRequest,
  CategoryUpdateRequest,
  ProductCreateRequest,
  ProductUpdateRequest,
  VariantCreateRequest,
  VariantUpdateRequest
} from '../types';

// ==========================================
// 1. Users Queries & Mutations
// ==========================================

export function useUsersQuery(params?: { role?: string; is_active?: boolean; skip?: number; limit?: number }) {
  return useQuery({
    queryKey: queryKeys.users.list(params),
    queryFn: () => userService.getUsers(params),
    staleTime: 1000 * 60 * 2,
  });
}

export function useUserDetailQuery(id: string) {
  return useQuery({
    queryKey: queryKeys.users.detail(id),
    queryFn: () => userService.getUser(id),
    enabled: Boolean(id),
  });
}

export function useApproversQuery() {
  return useQuery({
    queryKey: queryKeys.users.approvers,
    queryFn: () => userService.getApprovers(),
    staleTime: 1000 * 60 * 5,
  });
}

export function useCreateUserMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AdminCreateUserRequest) => userService.createUser(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.users.all });
    },
  });
}

export function useAdminChangePasswordMutation() {
  return useMutation({
    mutationFn: ({ userId, newPassword }: { userId: string; newPassword: string }) =>
      userService.adminChangePassword(userId, newPassword),
  });
}

// ==========================================
// 2. Customers Queries & Mutations
// ==========================================

export function useCustomersQuery(params?: { search?: string; customer_tier_id?: string; is_active?: boolean; skip?: number; limit?: number }) {
  return useQuery({
    queryKey: queryKeys.customers.list(params),
    queryFn: () => customerService.getCustomers(params),
    staleTime: 1000 * 60 * 2,
  });
}

export function useCustomerDetailQuery(id: string) {
  return useQuery({
    queryKey: queryKeys.customers.detail(id),
    queryFn: () => customerService.getCustomer(id),
    enabled: Boolean(id),
  });
}

export function useCustomerQuotationsQuery(id: string) {
  return useQuery({
    queryKey: queryKeys.customers.quotations(id),
    queryFn: () => customerService.getCustomerQuotations(id),
    enabled: Boolean(id),
  });
}

export function useCustomerOrdersQuery(id: string) {
  return useQuery({
    queryKey: queryKeys.customers.orders(id),
    queryFn: () => customerService.getCustomerOrders(id),
    enabled: Boolean(id),
  });
}

export function useCustomerSubscriptionsQuery(id: string) {
  return useQuery({
    queryKey: queryKeys.customers.subscriptions(id),
    queryFn: () => customerService.getCustomerSubscriptions(id),
    enabled: Boolean(id),
  });
}

export function useCreateCustomerMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CustomerCreateRequest) => customerService.createCustomer(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.customers.all });
    },
  });
}

export function useUpdateCustomerMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CustomerUpdateRequest }) =>
      customerService.updateCustomer(id, payload),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.customers.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.customers.detail(id) });
    },
  });
}

export function useDeleteCustomerMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => customerService.deleteCustomer(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.customers.all });
    },
  });
}

// ==========================================
// 3. Customer Tiers Queries & Mutations
// ==========================================

export function useCustomerTiersQuery(params?: { is_active?: boolean; skip?: number; limit?: number }) {
  return useQuery({
    queryKey: queryKeys.customerTiers.list(params),
    queryFn: () => customerTierService.getCustomerTiers(params),
    staleTime: 1000 * 60 * 5,
  });
}

export function useCustomerTierDetailQuery(id: string) {
  return useQuery({
    queryKey: queryKeys.customerTiers.detail(id),
    queryFn: () => customerTierService.getCustomerTier(id),
    enabled: Boolean(id),
  });
}

export function useCreateCustomerTierMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CustomerTierCreateRequest) => customerTierService.createCustomerTier(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.customerTiers.all });
    },
  });
}

export function useUpdateCustomerTierMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CustomerTierUpdateRequest }) =>
      customerTierService.updateCustomerTier(id, payload),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.customerTiers.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.customerTiers.detail(id) });
    },
  });
}

export function useDeleteCustomerTierMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => customerTierService.deleteCustomerTier(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.customerTiers.all });
    },
  });
}

// ==========================================
// 4. Product Categories Queries & Mutations
// ==========================================

export function useProductCategoriesQuery() {
  return useQuery({
    queryKey: queryKeys.productCategories.all,
    queryFn: () => catalogService.getCategories(),
    retry: 1,
  });
}

export function useCreateProductCategoryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CategoryCreateRequest) => catalogService.createCategory(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.productCategories.all });
    },
  });
}

export function useUpdateProductCategoryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CategoryUpdateRequest }) =>
      catalogService.updateCategory(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.productCategories.all });
    },
  });
}

export function useDeleteProductCategoryMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => catalogService.deleteCategory(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.productCategories.all });
    },
  });
}

// ==========================================
// 5. Products Queries & Mutations
// ==========================================

export function useProductsQuery() {
  return useQuery({
    queryKey: queryKeys.products.all,
    queryFn: () => catalogService.getProducts(),
    retry: 1,
  });
}

export function useProductDetailQuery(id: string) {
  return useQuery({
    queryKey: queryKeys.products.detail(id),
    queryFn: () => catalogService.getProduct(id),
    enabled: Boolean(id),
    retry: 1,
  });
}

export function useProductVariantsQuery(productId: string) {
  return useQuery({
    queryKey: queryKeys.products.variants(productId),
    queryFn: () => catalogService.getProductVariants(productId),
    enabled: Boolean(productId),
    retry: 1,
  });
}

export function useCreateProductMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProductCreateRequest) => catalogService.createProduct(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.products.all });
    },
  });
}

export function useUpdateProductMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ProductUpdateRequest }) =>
      catalogService.updateProduct(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.products.all });
    },
  });
}

export function useDeleteProductMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => catalogService.deleteProduct(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.products.all });
    },
  });
}

// ==========================================
// 6. Product Variants Mutations
// ==========================================

export function useCreateVariantMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ productId, payload }: { productId: string; payload: VariantCreateRequest }) =>
      catalogService.createVariant(productId, payload),
    onSuccess: (_, { productId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.products.variants(productId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.variants.all });
    },
  });
}

export function useUpdateVariantMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: VariantUpdateRequest }) =>
      catalogService.updateVariant(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.variants.all });
    },
  });
}

export function useDeleteVariantMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => catalogService.deleteVariant(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.variants.all });
    },
  });
}
