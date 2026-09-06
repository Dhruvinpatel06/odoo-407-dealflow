import React, { useState, useEffect, useCallback } from 'react';
import { 
  ShieldCheck, 
  Sliders, 
  Percent, 
  Save, 
  Package, 
  Warehouse as WarehouseIcon, 
  Repeat, 
  DollarSign, 
  Boxes,
  Users,
  UserPlus,
  Mail,
  Lock,
  Eye,
  EyeOff,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  X,
  Loader2,
  Building2,
  KeyRound
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { useQuery } from '@tanstack/react-query';
import { userService, warehouseService, subscriptionService, UserAdminError } from '../../services/api';
import { UserResponse, AdminCreateUserRequest } from '../../types';
import { CustomerManagementPanel } from './CustomerManagementPanel';
import { CustomerTierManagementPanel } from './CustomerTierManagementPanel';
import { AccessRestrictedView } from '../common/AccessRestrictedView';
import { useProductsQuery } from '../../hooks/useBackendData';

type AdminTab = 'DISCOUNTS' | 'CUSTOMERS' | 'CUSTOMER_TIERS' | 'CATALOG' | 'WAREHOUSES' | 'SUBSCRIPTIONS' | 'RISK' | 'USERS';

const PAGE_TO_TAB: Record<string, AdminTab> = {
  'discount-ceilings': 'DISCOUNTS',
  'customers-accounts': 'CUSTOMERS',
  'customer-tiers': 'CUSTOMER_TIERS',
  'catalog-pricelists': 'CATALOG',
  'warehouses-stock': 'WAREHOUSES',
  'subscriptions-billing': 'SUBSCRIPTIONS',
  'risk-margins': 'RISK',
  'users-access': 'USERS',
  'admin': 'DISCOUNTS',
  'admin-config': 'DISCOUNTS'
};

const TAB_TO_PAGE: Record<AdminTab, string> = {
  'DISCOUNTS': 'discount-ceilings',
  'CUSTOMERS': 'customers-accounts',
  'CUSTOMER_TIERS': 'customer-tiers',
  'CATALOG': 'catalog-pricelists',
  'WAREHOUSES': 'warehouses-stock',
  'SUBSCRIPTIONS': 'subscriptions-billing',
  'RISK': 'risk-margins',
  'USERS': 'users-access'
};

const TAB_INFO: Record<AdminTab, { title: string; subtitle: string; tag: string }> = {
  DISCOUNTS: {
    title: 'Discount Ceilings & Tiers',
    subtitle: 'Authoritative discount ceilings by sales role, customer tier, and product category (BR-01, BR-02).',
    tag: 'Policy Governance'
  },
  CUSTOMERS: {
    title: 'Customer Accounts & Portals',
    subtitle: 'Authoritative commercial customer profiles, payment terms, tiers, and commercial history.',
    tag: 'Customer Directory'
  },
  CUSTOMER_TIERS: {
    title: 'Customer Tier Governance & Ceilings',
    subtitle: 'Discount ceilings, min spend eligibility, and commercial privilege matrix.',
    tag: 'Tier Governance'
  },
  CATALOG: {
    title: 'Catalog & Price Lists',
    subtitle: 'Manage SKUs, list pricing, unit costs, and category discount limitations.',
    tag: 'Products & Rules'
  },
  WAREHOUSES: {
    title: 'Warehouses & Stock Allocation',
    subtitle: 'Facility routing rules, shipping weight factors, and multi-location inventory.',
    tag: 'Facility Routing'
  },
  SUBSCRIPTIONS: {
    title: 'Subscriptions & Recurring Billing',
    subtitle: 'Recurring service schedules, proration calculation engine, and billing cadence.',
    tag: 'Recurring Plans'
  },
  RISK: {
    title: 'Risk Scoring & Margin Protection',
    subtitle: 'Corporate margin floor (BR-04), hard stop policy thresholds, and composite risk weights.',
    tag: 'Risk Thresholds'
  },
  USERS: {
    title: 'Users & Access Administration',
    subtitle: 'Active system identities, RBAC assignments, and provisioning via backend authentication service.',
    tag: 'Active RBAC'
  }
};

export const AdminConfigView: React.FC = () => {
  const { 
    showNotification, 
    currentUser, 
    accessToken,
    currentPage,
    setCurrentPage
  } = useApp();

  const { data: products = [] } = useProductsQuery();
  const { data: warehouses = [] } = useQuery({
    queryKey: ['admin-warehouses'],
    queryFn: () => warehouseService.listWarehouses(),
  });
  const { data: subscriptions = [] } = useQuery({
    queryKey: ['admin-subscriptions'],
    queryFn: () => subscriptionService.listSubscriptions(),
  });

  const activeTab: AdminTab = PAGE_TO_TAB[currentPage] || 'DISCOUNTS';

  const handleTabClick = (tab: AdminTab) => {
    setCurrentPage(TAB_TO_PAGE[tab]);
  };

  // Users Management State
  const [usersList, setUsersList] = useState<UserResponse[]>([]);
  const [isUsersLoading, setIsUsersLoading] = useState<boolean>(false);
  const [usersError, setUsersError] = useState<string | null>(null);
  const [isAddUserOpen, setIsAddUserOpen] = useState<boolean>(false);

  // Add User Form State
  const [newUserName, setNewUserName] = useState<string>('');
  const [newUserEmail, setNewUserEmail] = useState<string>('');
  const [newUserPassword, setNewUserPassword] = useState<string>('');
  const [newUserRole, setNewUserRole] = useState<'CUSTOMER' | 'SALES_REP' | 'SALES_MANAGER' | 'FINANCE_OPERATIONS' | 'ADMIN'>('SALES_REP');
  const [newUserCustomerId, setNewUserCustomerId] = useState<string>('');
  const [newUserIsActive, setNewUserIsActive] = useState<boolean>(true);
  const [showNewUserPassword, setShowNewUserPassword] = useState<boolean>(false);
  const [isCreatingUser, setIsCreatingUser] = useState<boolean>(false);
  const [addUserFormError, setAddUserFormError] = useState<string | null>(null);

  // Admin Reset Password State
  const [resetUser, setResetUser] = useState<UserResponse | null>(null);
  const [resetPasswordValue, setResetPasswordValue] = useState<string>('');
  const [isResettingPassword, setIsResettingPassword] = useState<boolean>(false);
  const [resetPasswordError, setResetPasswordError] = useState<string | null>(null);
  const [showResetPassword, setShowResetPassword] = useState<boolean>(false);

  // Catalog queries from backend (with graceful fallback)
  const { data: backendProducts, isLoading: isCatalogLoading } = useProductsQuery();

  const handleAdminResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resetUser || isResettingPassword) return;
    if (!resetPasswordValue || resetPasswordValue.length < 8) {
      setResetPasswordError('Password must be at least 8 characters in length.');
      return;
    }
    setIsResettingPassword(true);
    setResetPasswordError(null);
    try {
      await userService.adminChangePassword(resetUser.id, resetPasswordValue);
      showNotification(`Password for "${resetUser.name}" reset successfully.`, 'success');
      setResetUser(null);
      setResetPasswordValue('');
    } catch (err: unknown) {
      if (err instanceof UserAdminError) {
        setResetPasswordError(err.message);
      } else if (err instanceof Error) {
        setResetPasswordError(err.message);
      } else {
        setResetPasswordError('Failed to reset user password.');
      }
    } finally {
      setIsResettingPassword(false);
    }
  };

  const fetchUsers = useCallback(async () => {
    setIsUsersLoading(true);
    setUsersError(null);
    try {
      const data = await userService.getUsers();
      setUsersList(data);
    } catch (err: unknown) {
      if (err instanceof UserAdminError) {
        setUsersError(err.message);
      } else {
        setUsersError('Failed to load users from the server.');
      }
    } finally {
      setIsUsersLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'USERS') {
      fetchUsers();
    }
  }, [activeTab, fetchUsers]);

  const handleAddUserSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isCreatingUser) return;

    if (!newUserName.trim()) {
      setAddUserFormError('Please enter user name.');
      return;
    }
    if (!newUserEmail.trim()) {
      setAddUserFormError('Please enter user email address.');
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(newUserEmail.trim())) {
      setAddUserFormError('Please enter a valid email address.');
      return;
    }
    if (!newUserPassword) {
      setAddUserFormError('Please enter a password.');
      return;
    }
    if (newUserPassword.length < 8) {
      setAddUserFormError('Password must be at least 8 characters in length.');
      return;
    }

    setIsCreatingUser(true);
    setAddUserFormError(null);

    try {
      const payload: AdminCreateUserRequest = {
        name: newUserName.trim(),
        email: newUserEmail.trim(),
        password: newUserPassword,
        role: newUserRole,
        is_active: newUserIsActive,
      };

      if (newUserCustomerId.trim()) {
        payload.customer_id = newUserCustomerId.trim();
      }

      await userService.createUser(payload);

      // 201 -> close/reset form, show success feedback, and refresh Users list
      showNotification(`User "${newUserName.trim()}" created successfully.`, 'success');
      setNewUserName('');
      setNewUserEmail('');
      setNewUserPassword('');
      setNewUserRole('SALES_REP');
      setNewUserCustomerId('');
      setNewUserIsActive(true);
      setIsAddUserOpen(false);
      await fetchUsers();
    } catch (err: unknown) {
      if (err instanceof UserAdminError) {
        setAddUserFormError(err.message);
      } else if (err instanceof Error) {
        setAddUserFormError(err.message);
      } else {
        setAddUserFormError('An unexpected error occurred while creating user.');
      }
    } finally {
      setIsCreatingUser(false);
    }
  };


  // Local state initialized from localStorage/defaults
  const [repCeiling, setRepCeiling] = useState(10);
  const [managerCeiling, setManagerCeiling] = useState(20);
  const [financeCeiling, setFinanceCeiling] = useState(30);
  const [minMarginFloor, setMinMarginFloor] = useState(25);
  
  const [tierPlatinum, setTierPlatinum] = useState(25);
  const [tierGold, setTierGold] = useState(18);
  const [tierSilver, setTierSilver] = useState(12);
  const [tierBronze, setTierBronze] = useState(8);

  const [catHardware, setCatHardware] = useState(15);
  const [catSubscription, setCatSubscription] = useState(25);
  const [catServices, setCatServices] = useState(20);

  const [riskThresholdManager, setRiskThresholdManager] = useState(35);
  const [riskThresholdFinance, setRiskThresholdFinance] = useState(65);

  const [riskWeightDiscount, setRiskWeightDiscount] = useState(40);
  const [riskWeightMargin, setRiskWeightMargin] = useState(35);
  const [riskWeightPayment, setRiskWeightPayment] = useState(25);

  const handleSavePolicy = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('dealflow_gov_admin_config', JSON.stringify({
      repCeiling, managerCeiling, financeCeiling, minMarginFloor,
      tierPlatinum, tierGold, tierSilver, tierBronze,
      catHardware, catSubscription, catServices,
      riskThresholdManager, riskThresholdFinance,
      riskWeightDiscount, riskWeightMargin, riskWeightPayment
    }));
    showNotification('Commercial governance policies committed to system configuration.', 'success');
  };

  // Defense-in-depth RBAC check (evaluated after all React hooks have run)
  if ((currentUser.role || '').toUpperCase() !== 'ADMIN') {
    return (
      <AccessRestrictedView
        requiredRole="Platform Administrator (Alex Mercer)"
        featureName="System Governance & Policy Administration"
      />
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
              System Governance &bull; {TAB_INFO[activeTab].tag}
            </span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            {TAB_INFO[activeTab].title}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {TAB_INFO[activeTab].subtitle}
          </p>
        </div>

        {activeTab !== 'USERS' && activeTab !== 'CUSTOMERS' && activeTab !== 'CUSTOMER_TIERS' && (
          <button
            onClick={handleSavePolicy}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Save Governance Policies</span>
          </button>
        )}
      </div>

      {/* Governance Navigation Tabs */}
      <div className="flex border-b border-gray-200 overflow-x-auto gap-2">
        <button
          onClick={() => handleTabClick('DISCOUNTS')}
          className={`pb-3 px-3 text-xs font-bold border-b-2 transition flex items-center gap-2 cursor-pointer shrink-0 ${
            activeTab === 'DISCOUNTS' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Percent className="w-3.5 h-3.5" />
          <span>1. Discount Ceilings</span>
        </button>

        <button
          onClick={() => handleTabClick('CUSTOMERS')}
          className={`pb-3 px-3 text-xs font-bold border-b-2 transition flex items-center gap-2 cursor-pointer shrink-0 ${
            activeTab === 'CUSTOMERS' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Building2 className="w-3.5 h-3.5" />
          <span>2. Customers & Accounts</span>
        </button>

        <button
          onClick={() => handleTabClick('CUSTOMER_TIERS')}
          className={`pb-3 px-3 text-xs font-bold border-b-2 transition flex items-center gap-2 cursor-pointer shrink-0 ${
            activeTab === 'CUSTOMER_TIERS' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>3. Customer Tiers</span>
        </button>

        <button
          onClick={() => handleTabClick('CATALOG')}
          className={`pb-3 px-3 text-xs font-bold border-b-2 transition flex items-center gap-2 cursor-pointer shrink-0 ${
            activeTab === 'CATALOG' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Package className="w-3.5 h-3.5" />
          <span>4. Catalog & Price Lists</span>
        </button>

        <button
          onClick={() => handleTabClick('WAREHOUSES')}
          className={`pb-3 px-3 text-xs font-bold border-b-2 transition flex items-center gap-2 cursor-pointer shrink-0 ${
            activeTab === 'WAREHOUSES' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <WarehouseIcon className="w-3.5 h-3.5" />
          <span>5. Warehouses & Stock</span>
        </button>

        <button
          onClick={() => handleTabClick('SUBSCRIPTIONS')}
          className={`pb-3 px-3 text-xs font-bold border-b-2 transition flex items-center gap-2 cursor-pointer shrink-0 ${
            activeTab === 'SUBSCRIPTIONS' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Repeat className="w-3.5 h-3.5" />
          <span>6. Subscriptions & Billing</span>
        </button>

        <button
          onClick={() => handleTabClick('RISK')}
          className={`pb-3 px-3 text-xs font-bold border-b-2 transition flex items-center gap-2 cursor-pointer shrink-0 ${
            activeTab === 'RISK' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>7. Risk Scoring & Margin</span>
        </button>

        <button
          onClick={() => handleTabClick('USERS')}
          className={`pb-3 px-3 text-xs font-bold border-b-2 transition flex items-center gap-2 cursor-pointer shrink-0 ${
            activeTab === 'USERS' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Users className="w-3.5 h-3.5" />
          <span>8. Users & Access</span>
        </button>
      </div>

      {/* Tab: Customers & Accounts */}
      {activeTab === 'CUSTOMERS' && (
        <CustomerManagementPanel />
      )}

      {/* Tab: Customer Tiers */}
      {activeTab === 'CUSTOMER_TIERS' && (
        <CustomerTierManagementPanel />
      )}


      {/* Tab 1: Discount Ceilings */}
      {activeTab === 'DISCOUNTS' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Ceilings by Role */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
              <Percent className="w-4 h-4 text-blue-600" />
              <h3 className="text-sm font-bold text-slate-900">Discount Ceilings by Role</h3>
            </div>

            <div className="space-y-3.5 text-xs">
              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Sales Representative Discretion:</span>
                  <span className="font-mono font-bold text-blue-600">≤ {repCeiling}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="15"
                  value={repCeiling}
                  onChange={(e) => setRepCeiling(parseInt(e.target.value))}
                  className="w-full accent-blue-600"
                />
                <span className="text-[11px] text-slate-400">Discounts at or below {repCeiling}% do not require approval unless margin floor breached.</span>
              </div>

              <div className="pt-2 border-t border-slate-100">
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Sales Manager Discretion:</span>
                  <span className="font-mono font-bold text-blue-600">≤ {managerCeiling}%</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="25"
                  value={managerCeiling}
                  onChange={(e) => setManagerCeiling(parseInt(e.target.value))}
                  className="w-full accent-blue-600"
                />
                <span className="text-[11px] text-slate-400">Requires Single-Level (Manager) approval when exceeding {repCeiling}%.</span>
              </div>

              <div className="pt-2 border-t border-slate-100">
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Finance & RevOps Ceiling:</span>
                  <span className="font-mono font-bold text-purple-600">&gt; {managerCeiling}% (Max {financeCeiling}%)</span>
                </div>
                <input
                  type="range"
                  min="20"
                  max="50"
                  value={financeCeiling}
                  onChange={(e) => setFinanceCeiling(parseInt(e.target.value))}
                  className="w-full accent-purple-600"
                />
                <span className="text-[11px] text-slate-400">Triggers sequential two-tier approval (Manager → Finance) automatically.</span>
              </div>
            </div>
          </div>

          {/* Customer Tier Ceilings */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
              <ShieldCheck className="w-4 h-4 text-amber-600" />
              <h3 className="text-sm font-bold text-slate-900">Customer Tier Ceilings</h3>
            </div>

            <div className="space-y-3.5 text-xs">
              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Platinum Tier Ceiling:</span>
                  <span className="font-mono font-bold text-amber-600">{tierPlatinum}%</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="35"
                  value={tierPlatinum}
                  onChange={(e) => setTierPlatinum(parseInt(e.target.value))}
                  className="w-full accent-amber-600"
                />
              </div>

              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Gold Tier Ceiling:</span>
                  <span className="font-mono font-bold text-amber-600">{tierGold}%</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="25"
                  value={tierGold}
                  onChange={(e) => setTierGold(parseInt(e.target.value))}
                  className="w-full accent-amber-600"
                />
              </div>

              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Silver Tier Ceiling:</span>
                  <span className="font-mono font-bold text-amber-600">{tierSilver}%</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="20"
                  value={tierSilver}
                  onChange={(e) => setTierSilver(parseInt(e.target.value))}
                  className="w-full accent-amber-600"
                />
              </div>

              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Bronze Tier Ceiling:</span>
                  <span className="font-mono font-bold text-amber-600">{tierBronze}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="15"
                  value={tierBronze}
                  onChange={(e) => setTierBronze(parseInt(e.target.value))}
                  className="w-full accent-amber-600"
                />
              </div>
            </div>
          </div>

          {/* Product Category Ceilings */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
              <Sliders className="w-4 h-4 text-emerald-600" />
              <h3 className="text-sm font-bold text-slate-900">Product Category Ceilings</h3>
            </div>

            <div className="space-y-3.5 text-xs">
              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Hardware Products:</span>
                  <span className="font-mono font-bold text-emerald-600">{catHardware}% max</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="30"
                  value={catHardware}
                  onChange={(e) => setCatHardware(parseInt(e.target.value))}
                  className="w-full accent-emerald-600"
                />
              </div>

              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Subscription Software:</span>
                  <span className="font-mono font-bold text-emerald-600">{catSubscription}% max</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="40"
                  value={catSubscription}
                  onChange={(e) => setCatSubscription(parseInt(e.target.value))}
                  className="w-full accent-emerald-600"
                />
              </div>

              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Professional Services:</span>
                  <span className="font-mono font-bold text-emerald-600">{catServices}% max</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="25"
                  value={catServices}
                  onChange={(e) => setCatServices(parseInt(e.target.value))}
                  className="w-full accent-emerald-600"
                />
              </div>

              <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs">
                Authoritative Rule: Lowest ceiling applies between Customer Tier and Category (BR-02).
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Catalog & Price Lists */}
      {activeTab === 'CATALOG' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900">Configured Products & Pricing Tiers</h3>
            <span className="text-xs text-slate-400 font-mono">{products.length} Active SKUs</span>
          </div>
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[10px]">
                <th className="py-3 px-4">SKU / Product</th>
                <th className="py-3 px-3">Category</th>
                <th className="py-3 px-3">List Price</th>
                <th className="py-3 px-3">Unit Cost</th>
                <th className="py-3 px-3">Gross Margin</th>
                <th className="py-3 px-3">Discount Limit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {products.map((p) => {
                const unitPrice = Number(p.base_price ?? p.unit_price ?? p.list_price ?? 0);
                const unitCost = Number(p.cost_price ?? p.unit_cost ?? p.standard_cost ?? 0);
                const margin = unitPrice > 0 ? (((unitPrice - unitCost) / unitPrice) * 100).toFixed(1) : '35.0';
                const categoryName = typeof p.category === 'object' ? (p.category as any)?.name : (p.category_name || (typeof p.category === 'string' ? p.category : 'General'));
                const discountLimit = p.max_discount_percent ?? p.max_discount_ceiling ?? 20;
                return (
                  <tr key={p.id} className="hover:bg-slate-50/60">
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">{p.name}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{p.sku}</div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">
                        {categoryName}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono font-bold text-slate-900">${unitPrice.toLocaleString()}</td>
                    <td className="py-3 px-3 font-mono text-slate-600">${unitCost.toLocaleString()}</td>
                    <td className="py-3 px-3 font-mono font-semibold text-emerald-600">{margin}%</td>
                    <td className="py-3 px-3 font-mono font-semibold text-blue-600">{discountLimit}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 3: Warehouses & Stock */}
      {activeTab === 'WAREHOUSES' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {warehouses.map((wh) => (
            <div key={wh.id} className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
              <div className="flex justify-between items-center pb-2 border-b border-slate-100">
                <strong className="text-slate-900 text-sm">{wh.name}</strong>
                <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold text-[10px]">{wh.code}</span>
              </div>
              <p className="text-xs text-slate-500">Location: {wh.address || wh.name} &bull; Freight Factor: {Number(wh.shipping_cost_weight || 1)}x</p>
              <div className="text-xs space-y-1.5 pt-2">
                <span className="font-bold text-slate-700 block">Status:</span>
                <span className="inline-block px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-[10px] font-bold">
                  {wh.is_active ? 'Active Distribution Hub' : 'Inactive'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 4: Subscriptions & Billing */}
      {activeTab === 'SUBSCRIPTIONS' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900">Recurring Billing Schedules</h3>
            <span className="text-xs text-purple-600 font-mono font-semibold">Proration Engine Active</span>
          </div>
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[10px]">
                <th className="py-3 px-4">Service</th>
                <th className="py-3 px-3">Interval</th>
                <th className="py-3 px-3">Units</th>
                <th className="py-3 px-3">Rate</th>
                <th className="py-3 px-3">Next Bill Date</th>
                <th className="py-3 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {subscriptions.map((s: any) => (
                <tr key={s.id}>
                  <td className="py-3 px-4 font-bold text-slate-900">{s.product_name || s.productName || 'Subscription'}</td>
                  <td className="py-3 px-3 font-mono">{s.billing_interval || s.interval || 'MONTHLY'}</td>
                  <td className="py-3 px-3 font-mono font-semibold">{s.quantity}</td>
                  <td className="py-3 px-3 font-mono font-bold text-slate-900">${Number(s.unit_price || s.amount || 0).toLocaleString()}</td>
                  <td className="py-3 px-3 font-mono text-slate-500">{s.next_billing_date ? new Date(s.next_billing_date).toLocaleDateString() : '-'}</td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {s.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 5: Risk Scoring & Margin */}
      {activeTab === 'RISK' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <h3 className="text-sm font-bold text-slate-900">Corporate Margin Protection</h3>
            </div>

            <div className="space-y-3.5 text-xs">
              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Minimum Corporate Margin Floor:</span>
                  <span className="font-mono font-bold text-emerald-600">{minMarginFloor}%</span>
                </div>
                <input
                  type="range"
                  min="20"
                  max="40"
                  value={minMarginFloor}
                  onChange={(e) => setMinMarginFloor(parseInt(e.target.value))}
                  className="w-full accent-emerald-600"
                />
                <span className="text-[11px] text-slate-400">Any line item or blended deal falling below {minMarginFloor}% margin triggers mandatory Finance sign-off.</span>
              </div>

              <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs">
                <span className="font-bold block mb-1">Hard Floor Violation Policy:</span>
                Quotes with margin &lt; 20% are flagged as CRITICAL risk and require executive justification notes before submission.
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
              <Sliders className="w-4 h-4 text-purple-600" />
              <h3 className="text-sm font-bold text-slate-900">Governance Risk Weights</h3>
            </div>

            <div className="space-y-3.5 text-xs">
              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Discount Breach Weight:</span>
                  <span className="font-mono font-bold text-purple-600">{riskWeightDiscount}%</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="60"
                  value={riskWeightDiscount}
                  onChange={(e) => setRiskWeightDiscount(parseInt(e.target.value))}
                  className="w-full accent-purple-600"
                />
              </div>

              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Margin Deviation Weight:</span>
                  <span className="font-mono font-bold text-purple-600">{riskWeightMargin}%</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="60"
                  value={riskWeightMargin}
                  onChange={(e) => setRiskWeightMargin(parseInt(e.target.value))}
                  className="w-full accent-purple-600"
                />
              </div>

              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Payment Terms Sensitivity:</span>
                  <span className="font-mono font-bold text-purple-600">{riskWeightPayment}%</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="50"
                  value={riskWeightPayment}
                  onChange={(e) => setRiskWeightPayment(parseInt(e.target.value))}
                  className="w-full accent-purple-600"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 6: Users & Access */}
      {activeTab === 'USERS' && (
        <div className="space-y-6">
          {/* Top Bar for Users: Info + Add User Action */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">System Users & Authentication Access</h3>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                View platform identities, roles, and provision new enterprise users.
              </p>
            </div>

            <div className="flex items-center gap-2.5">
              <button
                onClick={fetchUsers}
                disabled={isUsersLoading}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition cursor-pointer disabled:opacity-50"
                title="Refresh users list"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isUsersLoading ? 'animate-spin text-blue-600' : ''}`} />
                <span>Refresh</span>
              </button>

              <button
                onClick={() => {
                  setAddUserFormError(null);
                  setIsAddUserOpen(true);
                }}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>Add User</span>
              </button>
            </div>
          </div>

          {/* Add User Modal / Overlay Form */}
          {isAddUserOpen && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4 animate-in fade-in duration-150">
              <div className="w-full max-w-md bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden">
                <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <UserPlus className="w-4 h-4 text-blue-600" />
                    <h4 className="text-sm font-bold text-slate-900">Add New System User</h4>
                  </div>
                  <button
                    onClick={() => {
                      if (!isCreatingUser) setIsAddUserOpen(false);
                    }}
                    disabled={isCreatingUser}
                    className="text-slate-400 hover:text-slate-600 p-1 rounded-md transition cursor-pointer disabled:opacity-50"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <form onSubmit={handleAddUserSubmit} className="p-6 space-y-4">
                  {addUserFormError && (
                    <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-600" />
                      <span>{addUserFormError}</span>
                    </div>
                  )}

                  {/* Name */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-800 mb-1.5">
                      Name <span className="text-rose-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={newUserName}
                      onChange={(e) => {
                        setNewUserName(e.target.value);
                        if (addUserFormError) setAddUserFormError(null);
                      }}
                      disabled={isCreatingUser}
                      placeholder="e.g. John Sales"
                      className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition disabled:bg-slate-50"
                    />
                  </div>

                  {/* Email */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-800 mb-1.5">
                      Email <span className="text-rose-500">*</span>
                    </label>
                    <input
                      type="email"
                      value={newUserEmail}
                      onChange={(e) => {
                        setNewUserEmail(e.target.value);
                        if (addUserFormError) setAddUserFormError(null);
                      }}
                      disabled={isCreatingUser}
                      placeholder="e.g. john.sales@test.com"
                      className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition disabled:bg-slate-50"
                    />
                  </div>

                  {/* Password */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-800 mb-1.5">
                      Password <span className="text-rose-500">*</span> <span className="text-slate-400 font-normal">(min 8 characters)</span>
                    </label>
                    <div className="relative">
                      <input
                        type={showNewUserPassword ? 'text' : 'password'}
                        value={newUserPassword}
                        onChange={(e) => {
                          setNewUserPassword(e.target.value);
                          if (addUserFormError) setAddUserFormError(null);
                        }}
                        disabled={isCreatingUser}
                        placeholder="••••••••"
                        className="w-full bg-white border border-slate-200 rounded-lg pl-3 pr-10 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition disabled:bg-slate-50"
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewUserPassword(!showNewUserPassword)}
                        disabled={isCreatingUser}
                        className="absolute right-3 top-2 text-slate-400 hover:text-slate-600 transition cursor-pointer"
                        title={showNewUserPassword ? 'Hide password' : 'Show password'}
                      >
                        {showNewUserPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {/* Role Dropdown */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-800 mb-1.5">
                      Role <span className="text-rose-500">*</span>
                    </label>
                    <select
                      value={newUserRole}
                      onChange={(e) => setNewUserRole(e.target.value as any)}
                      disabled={isCreatingUser}
                      className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition disabled:bg-slate-50 cursor-pointer"
                    >
                      <option value="CUSTOMER">CUSTOMER</option>
                      <option value="SALES_REP">SALES_REP</option>
                      <option value="SALES_MANAGER">SALES_MANAGER</option>
                      <option value="FINANCE_OPERATIONS">FINANCE_OPERATIONS</option>
                      <option value="ADMIN">ADMIN</option>
                    </select>
                  </div>

                  {/* Customer ID (Optional) */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-800 mb-1.5">
                      Customer ID <span className="text-slate-400 font-normal">(optional UUID)</span>
                    </label>
                    <input
                      type="text"
                      value={newUserCustomerId}
                      onChange={(e) => setNewUserCustomerId(e.target.value)}
                      disabled={isCreatingUser}
                      placeholder="Leave empty if not customer-associated"
                      className="w-full bg-white border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition disabled:bg-slate-50 font-mono"
                    />
                  </div>

                  {/* Active Status */}
                  <div className="flex items-center gap-2 pt-1">
                    <input
                      type="checkbox"
                      id="newUserActiveCheckbox"
                      checked={newUserIsActive}
                      onChange={(e) => setNewUserIsActive(e.target.checked)}
                      disabled={isCreatingUser}
                      className="w-4 h-4 rounded text-blue-600 accent-blue-600 focus:ring-blue-500 border-slate-300 cursor-pointer"
                    />
                    <label htmlFor="newUserActiveCheckbox" className="text-xs font-medium text-slate-700 cursor-pointer select-none">
                      Active account status (default enabled)
                    </label>
                  </div>

                  {/* Actions */}
                  <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setIsAddUserOpen(false)}
                      disabled={isCreatingUser}
                      className="px-3.5 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs font-semibold transition cursor-pointer disabled:opacity-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isCreatingUser}
                      className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-xs font-semibold shadow-xs transition flex items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed"
                    >
                      {isCreatingUser ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Creating User...</span>
                        </>
                      ) : (
                        <>
                          <UserPlus className="w-3.5 h-3.5" />
                          <span>Create User</span>
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}

          {/* Users Table Card */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">Registered System Accounts</h3>
              <span className="text-xs text-slate-500 font-mono">
                {usersList.length} Accounts
              </span>
            </div>

            {usersError && (
              <div className="m-4 p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-amber-600" />
                <span>{usersError}</span>
              </div>
            )}

            {isUsersLoading && usersList.length === 0 ? (
              <div className="p-12 text-center text-slate-400 text-xs flex flex-col items-center justify-center gap-2">
                <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                <span>Loading system users...</span>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[10px]">
                      <th className="py-3 px-4">User</th>
                      <th className="py-3 px-3">Role</th>
                      <th className="py-3 px-3">Status</th>
                      <th className="py-3 px-3">Customer Link</th>
                      <th className="py-3 px-3">Created</th>
                      <th className="py-3 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {usersList.map((u) => {
                      const roleBadgeColor = 
                        u.role === 'ADMIN' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                        u.role === 'SALES_MANAGER' ? 'bg-purple-50 text-purple-700 border-purple-200' :
                        u.role === 'SALES_REP' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                        u.role === 'FINANCE_OPERATIONS' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                        'bg-teal-50 text-teal-700 border-teal-200';

                      return (
                        <tr key={u.id} className="hover:bg-slate-50/60 transition">
                          <td className="py-3 px-4">
                            <div className="font-bold text-slate-900">{u.name}</div>
                            <div className="text-[11px] text-slate-500 font-mono">{u.email}</div>
                          </td>
                          <td className="py-3 px-3">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold border font-mono ${roleBadgeColor}`}>
                              {u.role}
                            </span>
                          </td>
                          <td className="py-3 px-3">
                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold border ${
                              u.is_active 
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                                : 'bg-slate-100 text-slate-500 border-slate-200'
                            }`}>
                              <span className={`w-1.5 h-1.5 rounded-full ${u.is_active ? 'bg-emerald-500' : 'bg-slate-400'}`}></span>
                              {u.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td className="py-3 px-3 font-mono text-[11px] text-slate-500">
                            {u.customer_id ? u.customer_id.substring(0, 8) + '...' : '—'}
                          </td>
                          <td className="py-3 px-3 text-[11px] text-slate-500 font-mono">
                            {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                          </td>
                          <td className="py-3 px-3 text-right">
                            <button
                              onClick={() => {
                                setResetUser(u);
                                setResetPasswordValue('');
                                setResetPasswordError(null);
                              }}
                              className="px-2 py-1 text-[11px] font-semibold text-slate-600 hover:text-amber-700 hover:bg-amber-50 rounded border border-slate-200 transition cursor-pointer inline-flex items-center gap-1"
                              title={`Reset password for ${u.name}`}
                            >
                              <KeyRound className="w-3 h-3 text-amber-600" />
                              <span>Reset Password</span>
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Admin Reset Password Modal */}
          {resetUser && (
            <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
              <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-150">
                <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                  <div className="flex items-center gap-2">
                    <KeyRound className="w-4 h-4 text-amber-600" />
                    <h3 className="text-sm font-bold text-slate-900">Reset User Password</h3>
                  </div>
                  <button
                    onClick={() => setResetUser(null)}
                    className="text-slate-400 hover:text-slate-600 transition cursor-pointer"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <form onSubmit={handleAdminResetPassword} className="p-5 space-y-4">
                  <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs">
                    Setting authoritative backend password for <strong>{resetUser.name}</strong> ({resetUser.email}).
                  </div>

                  {resetPasswordError && (
                    <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                      <span>{resetPasswordError}</span>
                    </div>
                  )}

                  <div>
                    <label className="block text-xs font-semibold text-slate-800 mb-1.5">
                      New Password <span className="text-rose-500">*</span> <span className="text-slate-400 font-normal">(min 8 characters)</span>
                    </label>
                    <div className="relative">
                      <input
                        type={showResetPassword ? 'text' : 'password'}
                        value={resetPasswordValue}
                        onChange={(e) => {
                          setResetPasswordValue(e.target.value);
                          if (resetPasswordError) setResetPasswordError(null);
                        }}
                        disabled={isResettingPassword}
                        placeholder="••••••••"
                        className="w-full bg-white border border-slate-200 rounded-lg pl-3 pr-10 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:ring-amber-500/20 focus:border-amber-600 transition disabled:bg-slate-50"
                        autoFocus
                      />
                      <button
                        type="button"
                        onClick={() => setShowResetPassword(!showResetPassword)}
                        disabled={isResettingPassword}
                        className="absolute right-3 top-2 text-slate-400 hover:text-slate-600 transition cursor-pointer"
                        title={showResetPassword ? 'Hide password' : 'Show password'}
                      >
                        {showResetPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setResetUser(null)}
                      disabled={isResettingPassword}
                      className="px-3.5 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs font-semibold transition cursor-pointer disabled:opacity-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isResettingPassword}
                      className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-700 disabled:bg-amber-400 text-white text-xs font-semibold shadow-xs transition flex items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed"
                    >
                      {isResettingPassword ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Updating...</span>
                        </>
                      ) : (
                        <span>Set New Password</span>
                      )}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
