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
  LucideIcon
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
    canAccessManagerGovernance: true, // Limited governance area for discount tiers & approval thresholds
    canAccessBilling: true,
    canAccessFulfillment: true,
    canEditFulfillment: false,
    canAccessHealth: true,
    canAccessReports: true,
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
    canAccessBilling: true,
    canAccessFulfillment: true,
    canEditFulfillment: true,
    canAccessHealth: true,
    canAccessReports: true,
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
  FULFILLMENT_OPERATOR: {
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
    canAccessFulfillment: true,
    canEditFulfillment: true,
    canAccessHealth: false,
    canAccessReports: false,
    isExternalCustomer: false,
  }
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

  const items: NavItemConfig[] = [
    { 
      id: 'dashboard', 
      label: normalizedRole === 'SALES_REP' ? 'My Pipeline' : normalizedRole === 'SALES_MANAGER' ? 'Team Dashboard' : 'Dashboard', 
      icon: LayoutDashboard 
    },
    { 
      id: 'quotations', 
      label: 'Quotations', 
      icon: FileText, 
      badge: '5' 
    }
  ];

  // For Sales Manager: Show Approvals PROMINENTLY directly at the top with highlight!
  if (normalizedRole === 'SALES_MANAGER') {
    items.splice(1, 0, {
      id: 'approvals',
      label: 'Approvals Queue',
      icon: CheckCircle2,
      alertBadge: pendingApprovalsCount > 0 ? `${pendingApprovalsCount} Action Required` : undefined,
      highlighted: true,
      roleNote: 'Manager Level 1 Sign-Off'
    });
  } else if (perms.canAccessApprovals) {
    items.push({
      id: 'approvals',
      label: normalizedRole === 'SALES_REP' ? 'My Submitted Approvals' : 'Approval Center',
      icon: CheckCircle2,
      alertBadge: pendingApprovalsCount > 0 ? `${pendingApprovalsCount}` : undefined,
      roleNote: normalizedRole === 'SALES_REP' ? 'Submitter View' : 'Tier 2 Finance'
    });
  }

  if (perms.canAccessFulfillment) {
    items.push({ 
      id: 'fulfillment', 
      label: normalizedRole === 'SALES_REP' ? 'Fulfillment Tracking' : 'Fulfillment', 
      icon: Truck, 
      badge: '1',
      roleNote: normalizedRole === 'SALES_REP' ? 'View-Only' : undefined
    });
  }

  if (perms.canAccessBilling) {
    items.push({ id: 'billing', label: 'Billing & Hybrid', icon: CreditCard });
  }

  if (perms.canAccessHealth) {
    items.push({ 
      id: 'deal-health', 
      label: 'Deal Health', 
      icon: Activity, 
      alertBadge: activeAlertsCount > 0 ? `${activeAlertsCount}` : undefined 
    });
  }

  if (perms.canAccessReports) {
    items.push({ id: 'reports', label: 'Reports & Analytics', icon: BarChart3 });
  }

  // Sales Manager limited governance area (Requirements Section 14)
  if (normalizedRole === 'SALES_MANAGER' && perms.canAccessManagerGovernance) {
    items.push({
      id: 'manager-governance',
      label: 'Governance Policies',
      icon: Settings,
      highlighted: false,
      roleNote: 'Policy Limits'
    });
  }

  // Hide 'Administration' for Sales Reps, Sales Managers, Finance Ops!
  // Only show for ADMIN
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
        restrictionsSummary: "Approvals shown prominently. Administration is hidden. Review and override capabilities enabled."
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
    case 'FULFILLMENT_OPERATOR':
      return {
        label: 'Fulfillment Operations',
        name: 'Carlos Ruiz',
        badgeColor: 'bg-sky-50 text-sky-700 border-sky-200',
        badgeDot: 'bg-sky-600',
        desc: 'Warehouse Logistics: Multi-facility order allocation and backorder management.',
        restrictionsSummary: 'Access to warehouse fulfillment tracking, allocation overrides, and inventory management.'
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
