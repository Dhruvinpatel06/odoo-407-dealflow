import { UserRole, ApprovalInstance, ApprovalStep } from '../types';
import { 
  LayoutDashboard, 
  FileText, 
  CheckCircle2, 
  Truck, 
  CreditCard, 
  Activity, 
  BarChart3, 
  Settings, 
  LucideIcon,
  Percent,
  Package,
  Warehouse,
  Repeat,
  Sliders,
  Users,
  Building2,
  ShieldCheck
} from 'lucide-react';

export interface RolePermissions {
  canAccessAdmin: boolean;
  canApproveQuotes: boolean;
  canAccessApprovals: boolean;
  isApprover: boolean;
  canViewInternalMargins: boolean;
  canViewUnitCosts: boolean;
  canViewRiskScores: boolean;
  canCreateQuotations: boolean;
  canEditGovernancePolicies: boolean;
  canAccessManagerGovernance: boolean;
  canAccessBilling: boolean;
  canAccessFulfillment: boolean;
  canEditFulfillment: boolean;
  canAccessHealth: boolean;
  canAccessReports: boolean;
  isExternalCustomer: boolean;
}

export const ROLE_PERMISSIONS: Record<UserRole, RolePermissions> = {
  SALES_REP: {
    canAccessAdmin: false,
    canApproveQuotes: false, // Sales reps cannot approve their own quotes
    canAccessApprovals: true, // They can track status of submitted quotes
    isApprover: false,
    canViewInternalMargins: true,
    canViewUnitCosts: false, // Reps see selling price & margin %, not backend raw unit COGS
    canViewRiskScores: true,
    canCreateQuotations: true,
    canEditGovernancePolicies: false,
    canAccessManagerGovernance: false,
    canAccessBilling: false,
    canAccessFulfillment: true, // View-only tracking enabled for Sales Rep
    canEditFulfillment: false, // Cannot edit or override warehouse allocation
    canAccessHealth: true,
    canAccessReports: false,
    isExternalCustomer: false,
  },
  SALES_MANAGER: {
    canAccessAdmin: false,
    canApproveQuotes: true, // Primary Level 1 approver
    canAccessApprovals: true,
    isApprover: true,
    canViewInternalMargins: true,
    canViewUnitCosts: true,
    canViewRiskScores: true,
    canCreateQuotations: true,
    canEditGovernancePolicies: false,
    canAccessManagerGovernance: true, // Configures discount tiers and approval chains
    canAccessBilling: false,           // Restricted to Finance & Operations / Admin
    canAccessFulfillment: false,       // Finance & Operations handles warehouse fulfillment
    canEditFulfillment: false,
    canAccessHealth: true,             // Monitors deal health
    canAccessReports: false,           // Restricted to Admin
    isExternalCustomer: false,
  },
  FINANCE_OPERATIONS: {
    canAccessAdmin: false,
    canApproveQuotes: true, // Level 2 approver for high risk/high discount
    canAccessApprovals: true,
    isApprover: true,
    canViewInternalMargins: true,
    canViewUnitCosts: true,
    canViewRiskScores: true,
    canCreateQuotations: false,
    canEditGovernancePolicies: false,
    canAccessManagerGovernance: false,
    canAccessBilling: true,            // Reconciles recurring billing and credit notes
    canAccessFulfillment: true,        // Manages warehouse fulfillment splits and backorders
    canEditFulfillment: true,
    canAccessHealth: false,            // Deal health is for Sales Rep / Sales Manager
    canAccessReports: false,           // Platform-wide reporting is for Admin
    isExternalCustomer: false,
  },
  ADMIN: {
    canAccessAdmin: true,
    canApproveQuotes: true,
    canAccessApprovals: true,
    isApprover: true,
    canViewInternalMargins: true,
    canViewUnitCosts: true,
    canViewRiskScores: true,
    canCreateQuotations: true,
    canEditGovernancePolicies: true,
    canAccessManagerGovernance: true,
    canAccessBilling: true,
    canAccessFulfillment: true,
    canEditFulfillment: true,
    canAccessHealth: true,
    canAccessReports: true,
    isExternalCustomer: false,
  },
  CUSTOMER_PORTAL: {
    canAccessAdmin: false,
    canApproveQuotes: false,
    canAccessApprovals: false,
    isApprover: false,
    canViewInternalMargins: false, // RESTRICTED in portal
    canViewUnitCosts: false, // RESTRICTED in portal
    canViewRiskScores: false, // RESTRICTED in portal
    canCreateQuotations: false,
    canEditGovernancePolicies: false,
    canAccessManagerGovernance: false,
    canAccessBilling: false,
    canAccessFulfillment: false,
    canEditFulfillment: false,
    canAccessHealth: false,
    canAccessReports: false,
    isExternalCustomer: true,
  },
  CUSTOMER: {
    canAccessAdmin: false,
    canApproveQuotes: false,
    canAccessApprovals: false,
    isApprover: false,
    canViewInternalMargins: false,
    canViewUnitCosts: false,
    canViewRiskScores: false,
    canCreateQuotations: false,
    canEditGovernancePolicies: false,
    canAccessManagerGovernance: false,
    canAccessBilling: false,
    canAccessFulfillment: false,
    canEditFulfillment: false,
    canAccessHealth: false,
    canAccessReports: false,
    isExternalCustomer: true,
  },
};

export function getPendingApprovalStep(approval?: ApprovalInstance): ApprovalStep | undefined {
  if (!approval || !approval.steps) return undefined;
  return approval.steps.find(s => s.status === 'PENDING');
}

export function getPendingApprovalRole(approval?: ApprovalInstance): 'SALES_MANAGER' | 'FINANCE_OPERATIONS' | undefined {
  return getPendingApprovalStep(approval)?.roleRequired;
}

export interface NavItemConfig {
  id: string;
  label: string;
  icon: LucideIcon;
  badge?: string;
  alertBadge?: string;
  highlighted?: boolean;
  roleNote?: string;
}

export function getRoleNavItems(
  role: UserRole | string, 
  pendingApprovalsCount: number, 
  activeAlertsCount: number
): NavItemConfig[] {
  const normalizedRole = (role ? String(role).toUpperCase() : '') as UserRole;
  const perms = ROLE_PERMISSIONS[normalizedRole] || ROLE_PERMISSIONS.SALES_REP;

  // External Customer has no internal sidebar navigation items
  if (perms.isExternalCustomer) {
    return [];
  }

  // Platform Administrator has dedicated System Governance responsibilities
  if (normalizedRole === 'ADMIN') {
    return [
      {
        id: 'dashboard',
        label: 'Dashboard',
        icon: LayoutDashboard
      },
      {
        id: 'customers-accounts',
        label: 'Customers & Accounts',
        icon: Building2,
        roleNote: 'Directory & Portals'
      },
      {
        id: 'customer-tiers',
        label: 'Customer Tiers',
        icon: ShieldCheck,
        roleNote: 'Tier Governance'
      },
      {
        id: 'discount-ceilings',
        label: 'Discount Ceilings',
        icon: Percent,
        roleNote: 'Policy Governance'
      },
      {
        id: 'catalog-pricelists',
        label: 'Catalog & Price Lists',
        icon: Package,
        roleNote: 'Products & Rules'
      },
      {
        id: 'warehouses-stock',
        label: 'Warehouses & Stock',
        icon: Warehouse,
        roleNote: 'Facility Routing'
      },
      {
        id: 'subscriptions-billing',
        label: 'Subscriptions & Billing',
        icon: Repeat,
        roleNote: 'Recurring Plans'
      },
      {
        id: 'risk-margins',
        label: 'Risk Scoring & Margins',
        icon: Sliders,
        roleNote: 'Thresholds'
      },
      {
        id: 'users-access',
        label: 'Users & Access',
        icon: Users,
        roleNote: 'Active RBAC'
      },
    ];
  }

  const items: NavItemConfig[] = [
    { 
      id: 'dashboard', 
      label: normalizedRole === 'SALES_REP' ? 'My Pipeline' : normalizedRole === 'SALES_MANAGER' ? 'Team Dashboard' : 'Dashboard', 
      icon: LayoutDashboard 
    }
  ];

  // For Sales Manager: Show Approvals Queue PROMINENTLY directly after dashboard
  if (normalizedRole === 'SALES_MANAGER') {
    items.push({
      id: 'approvals',
      label: 'Approvals Queue',
      icon: CheckCircle2,
      alertBadge: pendingApprovalsCount > 0 ? `${pendingApprovalsCount} Action Required` : undefined,
      highlighted: true,
      roleNote: 'Manager Level 1 Sign-Off'
    });
  }

  // Quotations: Only for roles that build or review commercial deals (Sales Rep and Sales Manager)
  if (perms.canCreateQuotations) {
    items.push({ 
      id: 'quotations', 
      label: 'Quotations', 
      icon: FileText, 
      badge: '5' 
    });
  }

  // For other roles with approval access (Sales Rep: submitted tracking; Finance: second-level approvals)
  if (normalizedRole !== 'SALES_MANAGER' && perms.canAccessApprovals) {
    items.push({
      id: 'approvals',
      label: normalizedRole === 'SALES_REP' ? 'My Submitted Approvals' : 'Approvals Center',
      icon: CheckCircle2,
      alertBadge: pendingApprovalsCount > 0 ? `${pendingApprovalsCount}` : undefined,
      roleNote: normalizedRole === 'SALES_REP' ? 'Submitter View' : 'Level 2 Sign-Off'
    });
  }

  // Sales Manager: Configures discount tiers and approval chains
  if (normalizedRole === 'SALES_MANAGER' && perms.canAccessManagerGovernance) {
    items.push({
      id: 'manager-governance',
      label: 'Discount Tiers & Approvals',
      icon: Sliders,
      highlighted: false,
      roleNote: 'Governance Thresholds'
    });
  }

  // Fulfillment: Sales Rep (tracking) and Finance/Operations (managing warehouse fulfillment splits and backorders)
  if (perms.canAccessFulfillment) {
    items.push({ 
      id: 'fulfillment', 
      label: normalizedRole === 'SALES_REP' ? 'Fulfillment Tracking' : 'Fulfillment & Allocation', 
      icon: Truck, 
      badge: '1',
      roleNote: normalizedRole === 'SALES_REP' ? 'View-Only' : 'Splits & Backorders'
    });
  }

  // Billing: Finance & Operations reconciles recurring billing and credit notes
  if (perms.canAccessBilling) {
    items.push({ 
      id: 'billing', 
      label: 'Billing & Subscriptions', 
      icon: CreditCard,
      roleNote: 'Reconciliation'
    });
  }



  if (perms.canAccessAdmin) {
    items.push({ 
      id: 'admin', 
      label: 'Administration', 
      icon: Settings,
      highlighted: false,
      roleNote: 'Admin Only'
    });
  }

  return items;
}


export function getRoleMeta(role: UserRole | string) {
  const normalizedRole = (role ? String(role).toUpperCase() : '') as UserRole;
  switch (normalizedRole) {
    case 'SALES_REP':
      return {
        label: 'Sales Representative',
        name: 'Sarah Chen',
        badgeColor: 'bg-blue-50 text-[#2563EB] border-blue-200',
        badgeDot: 'bg-[#2563EB]',
        desc: 'Pipeline creator: Drafts quotes, requests discount allowances, tracks approval state.',
        restrictionsSummary: "Administration is hidden. Approvals are in 'Submitter Tracking' mode with self-approval restricted."
      };
    case 'SALES_MANAGER':
      return {
        label: 'Sales Manager',
        name: 'Marcus Vance',
        badgeColor: 'bg-purple-50 text-purple-700 border-purple-200',
        badgeDot: 'bg-purple-600',
        desc: 'Commercial governor: Authoritative Level 1 approver for quotes exceeding rep discount limits.',
        restrictionsSummary: "Approvals queue & team radar active. Billing, reporting, and policy governance restricted to Finance/Admin."
      };
    case 'FINANCE_OPERATIONS':
      return {
        label: 'Finance & RevOps',
        name: 'Elena Rostova',
        badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        badgeDot: 'bg-emerald-600',
        desc: 'Profitability guard: Tier 2 approver for high risk/deep discount quotes and billing engine.',
        restrictionsSummary: "Access to raw unit COGS, billing, unbilled revenue, and high-risk Tier 2 sign-offs. Admin hidden."
      };
    case 'ADMIN':
      return {
        label: 'Platform Administrator',
        name: 'Alex Mercer',
        badgeColor: 'bg-amber-50 text-amber-800 border-amber-200',
        badgeDot: 'bg-amber-600',
        desc: 'Superuser: Full control over governance policies, RBAC matrices, and system configuration.',
        restrictionsSummary: "Unrestricted access to all views including Administration and immutable audit logs."
      };
    case 'CUSTOMER_PORTAL':
    case 'CUSTOMER':
      return {
        label: 'Customer Procurement',
        name: 'David Kross (Acme)',
        badgeColor: 'bg-teal-50 text-teal-800 border-teal-200',
        badgeDot: 'bg-teal-600',
        desc: 'External client: Reviews proposed deliverables, negotiated pricing, accepts or counters terms.',
        restrictionsSummary: "Strict data minimization: Internal margins, unit costs, risk scores, and approval notes are hidden."
      };

    default:
      return {
        label: 'User',
        name: 'DealFlow User',
        badgeColor: 'bg-gray-50 text-gray-700 border-gray-200',
        badgeDot: 'bg-gray-400',
        desc: 'General access',
        restrictionsSummary: 'Standard permissions'
      };
  }
}
