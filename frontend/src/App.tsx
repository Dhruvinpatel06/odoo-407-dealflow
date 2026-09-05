import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { Sidebar } from './components/layout/Sidebar';
import { DashboardView } from './components/dashboard/DashboardView';
import { QuotationsList } from './components/quotations/QuotationsList';
import { QuoteBuilder } from './components/quotations/QuoteBuilder';
import { ApprovalCenter } from './components/approvals/ApprovalCenter';
import { FulfillmentView } from './components/fulfillment/FulfillmentView';
import { BillingView } from './components/billing/BillingView';
import { CustomerPortal } from './components/portal/CustomerPortal';
import { DealHealthView } from './components/health/DealHealthView';
import { ReportsView } from './components/reports/ReportsView';
import { AdminConfigView } from './components/admin/AdminConfigView';
import { ManagerGovernanceView } from './components/governance/ManagerGovernanceView';
import { LoginView } from './components/auth/LoginView';
import { SignupView } from './components/auth/SignupView';
import { TestFlowGuideModal } from './components/common/TestFlowGuideModal';
import { AccessRestrictedView } from './components/common/AccessRestrictedView';
import { CheckCircle2, AlertTriangle, Info, X } from 'lucide-react';

const AppContent: React.FC = () => {
  const { currentPage, notification, currentUser } = useApp();

  // The Customer Portal has a dedicated, customer-branded layout without internal sidebars
  if (currentPage === 'portal' || currentPage === 'customer-portal') {
    return (
      <div className="min-h-screen bg-[#F9FAFB] font-sans text-[#111827]">
        <CustomerPortal />
        <TestFlowGuideModal />
        {/* Global Toast Notification */}
        {notification && (
          <div className="fixed bottom-5 right-5 z-50 animate-in fade-in slide-in-from-bottom-3 duration-200">
            <div className={`flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-lg text-xs font-semibold border ${
              notification.type === 'success' ? 'bg-emerald-900 text-emerald-100 border-emerald-700' :
              notification.type === 'error' ? 'bg-rose-900 text-rose-100 border-rose-700' :
              notification.type === 'warning' ? 'bg-amber-900 text-amber-100 border-amber-700' :
              'bg-[#111827] text-white border-slate-700'
            }`}>
              {notification.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
              {notification.type === 'error' && <AlertTriangle className="w-4 h-4 text-rose-400" />}
              {notification.type === 'warning' && <AlertTriangle className="w-4 h-4 text-amber-400" />}
              {notification.type === 'info' && <Info className="w-4 h-4 text-blue-400" />}
              <span>{notification.message}</span>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Full-screen Persona Switcher & Login
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
    // RBAC: If a non-admin attempts to view the Administration page, display access restriction
    if ((currentPage === 'admin' || currentPage === 'admin-config') && (currentUser.role || '').toUpperCase() !== 'ADMIN') {
      return (
        <AccessRestrictedView 
          requiredRole="Platform Administrator (Alex Mercer)" 
          featureName="System Administration & Configuration" 
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
      case 'deal-health':
        return <DealHealthView />;
      case 'reports':
        return <ReportsView />;
      case 'manager-governance':
        return <ManagerGovernanceView />;
      case 'admin':
      case 'admin-config':
        return <AdminConfigView />;
      default:
        return <DashboardView />;
    }
  };

  return (
    <div className="flex h-screen bg-[#F9FAFB] font-sans text-[#111827] overflow-hidden">
      {/* Permanent Enterprise Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <main className="flex-1 overflow-y-auto bg-[#F9FAFB]">
          {renderCurrentPage()}
        </main>
      </div>

      {/* Interactive Acceptance Test Guide Modal (Steps 1 to 8) */}
      <TestFlowGuideModal />

      {/* Global Toast Notification */}
      {notification && (
        <div className="fixed bottom-5 right-5 z-50 animate-in fade-in slide-in-from-bottom-3 duration-200">
          <div className={`flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-lg text-xs font-semibold border ${
            notification.type === 'success' ? 'bg-emerald-900 text-emerald-100 border-emerald-700' :
            notification.type === 'error' ? 'bg-rose-900 text-rose-100 border-rose-700' :
            notification.type === 'warning' ? 'bg-amber-900 text-amber-100 border-amber-700' :
            'bg-slate-900 text-slate-100 border-slate-700'
          }`}>
            {notification.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
            {notification.type === 'error' && <AlertTriangle className="w-4 h-4 text-rose-400" />}
            {notification.type === 'warning' && <AlertTriangle className="w-4 h-4 text-amber-400" />}
            {notification.type === 'info' && <Info className="w-4 h-4 text-blue-400" />}
            <span>{notification.message}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}
