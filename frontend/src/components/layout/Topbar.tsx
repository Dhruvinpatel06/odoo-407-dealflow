import React, { useState } from 'react';
import { 
  Search, 
  Bell, 
  RotateCw, 
  HelpCircle, 
  CheckCircle2, 
  ArrowRight
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const Topbar: React.FC = () => {
  const { 
    currentPage, 
    setCurrentPage, 
    currentUser, 
    recalculateActiveQuote, 
    dealAlerts, 
    showNotification,
    setIsGuideOpen 
  } = useApp();

  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showNotificationMenu, setShowNotificationMenu] = useState(false);

  const getPageMeta = () => {
    switch (currentPage) {
      case 'dashboard':
        return { title: 'Executive Operations Dashboard', breadcrumb: 'Sales Operations' };
      case 'quotations':
        return { title: 'Quotation Management', breadcrumb: 'Workspace / Deals' };
      case 'quote-builder':
        return { title: 'Quotation Builder & DealFlow Intelligence', breadcrumb: 'Quotation / Editor' };
      case 'approvals':
        return { title: 'Approval Center & Governance', breadcrumb: 'Operations / Governance' };
      case 'fulfillment':
        return { title: 'Multi-Warehouse Fulfillment & Allocation', breadcrumb: 'Supply Chain / Warehouse' };
      case 'billing':
        return { title: 'Hybrid Billing & Subscriptions', breadcrumb: 'Finance / Invoicing' };
      case 'deal-health':
        return { title: 'Deal Health & Anomaly Monitoring', breadcrumb: 'Intelligence / Risk' };
      case 'reports':
        return { title: 'Executive Analytics & Performance', breadcrumb: 'Intelligence / Reports' };
      case 'admin':
        return { title: 'Platform Administration & Configuration', breadcrumb: 'Settings / Configuration' };
      default:
        return { title: 'DealFlow360', breadcrumb: 'Sales Workspace' };
    }
  };

  const { title, breadcrumb } = getPageMeta();

  const handleReloadData = () => {
    setIsRefreshing(true);
    recalculateActiveQuote();
    setTimeout(() => {
      setIsRefreshing(false);
      showNotification('Refreshed authoritative pricing, warehouse inventory, and approval rules from FastAPI.', 'success');
    }, 600);
  };

  return (
    <header className="h-16 bg-white border-b border-gray-200 px-8 flex items-center justify-between shrink-0 z-10">
      {/* Breadcrumb & Title */}
      <div className="flex items-center gap-4 text-sm text-gray-500">
        <span>{breadcrumb}</span>
        <span className="text-gray-300">/</span>
        <span className="text-[#111827] font-medium">{title}</span>
      </div>

      {/* Right Controls matching Editorial Aesthetic */}
      <div className="flex items-center gap-4">
        {/* Search Bar - rounded-full editorial aesthetic */}
        <div className="relative hidden md:block">
          <input
            type="text"
            placeholder="Search deals, quotes, SKUs..."
            className="pl-10 pr-4 py-1.5 bg-gray-100 border-none rounded-full text-sm w-64 focus:ring-2 focus:ring-blue-500 text-gray-800 placeholder-gray-400 transition"
          />
          <Search className="w-4 h-4 absolute left-3.5 top-2 text-gray-400 pointer-events-none" />
        </div>

        {/* Reload Data Button */}
        <button
          onClick={handleReloadData}
          disabled={isRefreshing}
          title="Refreshes live pricing, inventory, and governance data"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-200 bg-white hover:bg-gray-50 text-gray-700 text-xs font-medium transition cursor-pointer"
        >
          <RotateCw className={`w-3.5 h-3.5 text-gray-500 ${isRefreshing ? 'animate-spin text-[#2563EB]' : ''}`} />
          <span className="hidden sm:inline">Reload</span>
        </button>

        {/* Quick Test Flow Walkthrough helper */}
        <button
          onClick={() => setIsGuideOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-50 hover:bg-blue-100 text-[#2563EB] text-xs font-semibold transition cursor-pointer"
        >
          <HelpCircle className="w-3.5 h-3.5 text-[#2563EB]" />
          <span>Demo Guide</span>
        </button>

        {/* Notification Bell matching Editorial Aesthetic */}
        <div className="relative">
          <button
            onClick={() => setShowNotificationMenu(!showNotificationMenu)}
            className="w-8 h-8 rounded-full border border-gray-200 hover:bg-gray-50 flex items-center justify-center relative text-gray-500 transition cursor-pointer"
          >
            <Bell className="w-4 h-4 text-gray-500" />
            <span className="absolute top-0 right-0 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white" />
          </button>

          {/* Notifications Dropdown */}
          {showNotificationMenu && (
            <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl border border-gray-200 shadow-xl py-2 z-50 text-xs">
              <div className="px-3 py-1.5 border-b border-gray-100 flex items-center justify-between">
                <span className="font-bold text-gray-800">Operational Alerts</span>
                <span className="text-[10px] bg-red-50 text-red-700 px-1.5 py-0.5 rounded-full font-bold">
                  {dealAlerts.length} Active
                </span>
              </div>
              <div className="max-h-64 overflow-y-auto divide-y divide-gray-100">
                {dealAlerts.slice(0, 3).map((alt) => (
                  <div 
                    key={alt.id} 
                    onClick={() => {
                      setCurrentPage('deal-health');
                      setShowNotificationMenu(false);
                    }}
                    className="p-3 hover:bg-gray-50 cursor-pointer transition"
                  >
                    <div className="flex items-center justify-between text-[11px] mb-1">
                      <span className="font-semibold text-gray-900">{alt.quoteNumber} — {alt.customerName}</span>
                      <span className="text-[10px] text-gray-400">{alt.ageDays}d ago</span>
                    </div>
                    <p className="text-gray-600 text-[11px] leading-relaxed line-clamp-2">{alt.reason}</p>
                  </div>
                ))}
              </div>
              <div className="p-2 border-t border-gray-100 text-center">
                <button 
                  onClick={() => {
                    setCurrentPage('deal-health');
                    setShowNotificationMenu(false);
                  }}
                  className="text-[#2563EB] font-semibold text-[11px] hover:underline cursor-pointer"
                >
                  View all in Deal Health →
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Current Persona Pill */}
        <div className="hidden lg:flex items-center gap-2 pl-2 border-l border-gray-200">
          <span className="text-[11px] font-medium text-gray-400">Role:</span>
          <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-800 font-mono">
            {currentUser.role.replace('_', ' ')}
          </span>
        </div>
      </div>
    </header>
  );
};
