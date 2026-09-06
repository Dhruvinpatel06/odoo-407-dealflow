import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Sidebar } from './components/layout/Sidebar';
import { DashboardView } from './components/dashboard/DashboardView';
import { QuotationsList } from './components/quotations/QuotationsList';
import { QuoteBuilder } from './components/quotations/QuoteBuilder';
import { ApprovalCenter } from './components/approvals/ApprovalCenter';
import { FulfillmentView } from './components/fulfillment/FulfillmentView';
import { BillingView } from './components/billing/BillingView';
import { CustomerPortal } from './components/portal/CustomerPortal';
import { AdminConfigView } from './components/admin/AdminConfigView';
import { ManagerGovernanceView } from './components/governance/ManagerGovernanceView';
import { LoginView } from './components/auth/LoginView';
import { SignupView } from './components/auth/SignupView';
import { TestFlowGuideModal } from './components/common/TestFlowGuideModal';
import { AccessRestrictedView } from './components/common/AccessRestrictedView';
import { UserRole } from './types';
import { ROLE_PERMISSIONS } from './utils/rbac';
import { CheckCircle2, AlertTriangle, Info } from 'lucide-react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 1000 * 60,
    },
  },
});

const AppContent: React.FC = () => {
  const { currentPage, notification, currentUser } = useApp();

  // The Customer Portal has a dedicated, customer-branded layout without internal sidebars
  if (currentPage === 'portal' || currentPage === 'customer-portal') {
    const normalizedRole = (currentUser.role ? String(currentUser.role).toUpperCase() : '') as UserRole;
    const perms = ROLE_PERMISSIONS[normalizedRole] || ROLE_PERMISSIONS.SALES_REP;

    if (!perms.isExternalCustomer) {
      return (
        <div className="flex h-screen bg-[#F9FAFB] font-sans text-[#111827] overflow-hidden">
          <Sidebar />
          <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
            <main className="flex-1 overflow-y-auto bg-[#F9FAFB]">
              <AccessRestrictedView 
                requiredRole="Customer / External Portal User" 
                featureName="Customer Collaboration Portal" 
              />
            </main>
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen bg-[#F9FAFB] font-sans text-[#111827]">
        <CustomerPortal />
        <TestFlowGuideModal />
        {notification && (
          <div className="fixed bottom-5 right-5 z-50 animate-in fade-in slide-in-from-bottom-3 duration-200">
            <div className={`flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-xl text-xs font-semibold border ${
              notification.type === 'success' ? 'bg-white text-emerald-800 border-emerald-200' :
              notification.type === 'error' ? 'bg-white text-rose-800 border-rose-200' :
              notification.type === 'warning' ? 'bg-white text-amber-800 border-amber-200' :
              'bg-white text-slate-800 border-slate-200'
            }`}>
              {notification.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
              {notification.type === 'error' && <AlertTriangle className="w-4 h-4 text-rose-600" />}
              {notification.type === 'warning' && <AlertTriangle className="w-4 h-4 text-amber-600" />}
              {notification.type === 'info' && <Info className="w-4 h-4 text-blue-600" />}
              <span>{notification.message}</span>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Full-screen Login
  if (currentPage === 'login') {
    return (
      <div className="min-h-screen bg-[#F9FAFB] font-sans text-[#111827]">
        <LoginView />
        <TestFlowGuideModal />
      </div>
    );
  }

  // Full-screen Public Registration
  if (currentPage === 'signup') {
    return (
      <div className="min-h-screen bg-[#F9FAFB] font-sans text-[#111827]">
        <SignupView />
        <TestFlowGuideModal />
      </div>
    );
  }

  // Standard Internal Enterprise Layout
  const renderCurrentPage = () => {
    const normalizedRole = (currentUser.role ? String(currentUser.role).toUpperCase() : '') as UserRole;
    const perms = ROLE_PERMISSIONS[normalizedRole] || ROLE_PERMISSIONS.SALES_REP;

    if (perms.isExternalCustomer) {
      return (
        <AccessRestrictedView 
          requiredRole="Internal Employee Console" 
          featureName="Internal Enterprise Workspace" 
        />
      );
    }

    const adminPages = [
      'admin', 'admin-config', 'discount-ceilings', 'customers-accounts',
      'customer-tiers', 'catalog-pricelists', 'warehouses-stock',
      'subscriptions-billing', 'risk-margins', 'users-access'
    ];

    if (adminPages.includes(currentPage) && normalizedRole !== 'ADMIN') {
      return (
        <AccessRestrictedView 
          requiredRole="Platform Administrator" 
          featureName="System Governance & Policy Administration" 
        />
      );
    }

    if ((currentPage === 'quotations' || currentPage === 'quote-builder' || currentPage === 'pipeline') && !perms.canCreateQuotations && normalizedRole !== 'ADMIN') {
      return (
        <AccessRestrictedView 
          requiredRole="Sales Representative or Sales Manager" 
          featureName="Quotation Management & DealFlow Intelligence" 
        />
      );
    }

    if (currentPage === 'fulfillment' && !perms.canAccessFulfillment) {
      return (
        <AccessRestrictedView 
          requiredRole="Finance & RevOps or Sales Representative" 
          featureName="Multi-Warehouse Fulfillment & Allocation" 
        />
      );
    }

    if (currentPage === 'billing' && !perms.canAccessBilling) {
      return (
        <AccessRestrictedView 
          requiredRole="Finance & RevOps or Administrator" 
          featureName="Hybrid Billing & Recurring Subscriptions" 
        />
      );
    }

    if (currentPage === 'manager-governance' && !perms.canAccessManagerGovernance) {
      return (
        <AccessRestrictedView 
          requiredRole="Sales Manager or Administrator" 
          featureName="Sales Operations Governance & Thresholds" 
        />
      );
    }

    switch (currentPage) {
      case 'dashboard':
        return <DashboardView />;
      case 'quotations':
        return <QuotationsList />;
      case 'pipeline':
        return <QuotationsList initialViewMode="kanban" />;
      case 'quote-builder':
        return <QuoteBuilder />;
      case 'approvals':
        return <ApprovalCenter />;
      case 'fulfillment':
        return <FulfillmentView />;
      case 'billing':
        return <BillingView />;
      case 'manager-governance':
        return <ManagerGovernanceView />;
      case 'admin':
      case 'admin-config':
      case 'discount-ceilings':
      case 'customers-accounts':
      case 'customer-tiers':
      case 'catalog-pricelists':
      case 'warehouses-stock':
      case 'subscriptions-billing':
      case 'risk-margins':
      case 'users-access':
        return <AdminConfigView />;
      default:
        return <DashboardView />;
    }
  };

  return (
    <div className="flex h-screen bg-[#F9FAFB] font-sans text-[#111827] overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <main className="flex-1 overflow-y-auto bg-[#F9FAFB]">
          {renderCurrentPage()}
        </main>
      </div>
      <TestFlowGuideModal />
      {notification && (
        <div className="fixed bottom-5 right-5 z-50 animate-in fade-in slide-in-from-bottom-3 duration-200">
          <div className={`flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-xl text-xs font-semibold border ${
            notification.type === 'success' ? 'bg-white text-emerald-800 border-emerald-200' :
            notification.type === 'error' ? 'bg-white text-rose-800 border-rose-200' :
            notification.type === 'warning' ? 'bg-white text-amber-800 border-amber-200' :
            'bg-white text-slate-800 border-slate-200'
          }`}>
            {notification.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
            {notification.type === 'error' && <AlertTriangle className="w-4 h-4 text-rose-600" />}
            {notification.type === 'warning' && <AlertTriangle className="w-4 h-4 text-amber-600" />}
            {notification.type === 'info' && <Info className="w-4 h-4 text-blue-600" />}
            <span>{notification.message}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppProvider>
        <AppContent />
      </AppProvider>
    </QueryClientProvider>
  );
}
