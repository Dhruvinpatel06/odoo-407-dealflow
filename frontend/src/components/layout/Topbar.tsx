import React, { useState } from 'react';
import { 
  Search, 
  Bell, 
  RotateCw, 
  HelpCircle, 
  CheckCircle2, 
  ArrowRight,
  LogOut,
  KeyRound,
  Eye,
  EyeOff,
  AlertCircle,
  X,
  Loader2
} from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { useApp } from '../../context/AppContext';
import { authService } from '../../services/api';

export const Topbar: React.FC = () => {
  const { 
    currentPage, 
    setCurrentPage, 
    currentUser, 
    recalculateActiveQuote, 
    dealAlerts, 
    showNotification,
    setIsGuideOpen,
    resetDemoData,
    accessToken,
    refreshBackendCustomers
  } = useApp();

  const queryClient = useQueryClient();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showNotificationMenu, setShowNotificationMenu] = useState(false);

  // Change Password Modal State
  const [isChangePasswordOpen, setIsChangePasswordOpen] = useState(false);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [showOldPassword, setShowOldPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [changePasswordError, setChangePasswordError] = useState<string | null>(null);

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
      case 'manager-governance':
        return { title: 'Sales Operations Governance & Thresholds', breadcrumb: 'Management / Governance' };
      case 'admin':
      case 'admin-config':
        return { title: 'Platform Administration & Configuration', breadcrumb: 'Settings / Configuration' };
      default:
        return { title: 'DealFlow360', breadcrumb: 'Sales Workspace' };
    }
  };

  const { title, breadcrumb } = getPageMeta();

  const handleReloadData = async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        queryClient.invalidateQueries(),
        refreshBackendCustomers()
      ]);
      recalculateActiveQuote();
      showNotification('Refreshed authoritative pricing, customer records, and governance rules from FastAPI.', 'success');
    } catch {
      recalculateActiveQuote();
      showNotification('Refreshed local operational state.', 'info');
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleChangePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isChangingPassword) return;

    if (!oldPassword || !newPassword) {
      setChangePasswordError('Both current password and new password are required.');
      return;
    }
    if (newPassword.length < 8) {
      setChangePasswordError('New password must be at least 8 characters in length.');
      return;
    }

    setIsChangingPassword(true);
    setChangePasswordError(null);

    try {
      await authService.changePassword(oldPassword, newPassword);
      showNotification('Your password has been changed successfully.', 'success');
      setIsChangePasswordOpen(false);
      setOldPassword('');
      setNewPassword('');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to change password.';
      setChangePasswordError(msg);
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleResetData = () => {
    if (window.confirm('Reset all demo state (quotations, approvals, fulfillment, invoices) back to original seed data?')) {
      resetDemoData();
    }
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

        {/* Reset Demo Data Button */}
        <button
          onClick={handleResetData}
          title="Reset all demo quotes, approvals, and invoices to initial state"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-rose-200 bg-rose-50/50 hover:bg-rose-100 text-rose-700 text-xs font-medium transition cursor-pointer"
        >
          <span>Reset Demo</span>
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

        {/* Current Persona Pill, Password & Sign Out */}
        <div className="hidden lg:flex items-center gap-2 pl-2 border-l border-gray-200">
          <span className="text-[11px] font-medium text-gray-400">Role:</span>
          <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-800 font-mono">
            {currentUser.role.replace('_', ' ')}
          </span>

          <button
            onClick={() => {
              setIsChangePasswordOpen(true);
              setOldPassword('');
              setNewPassword('');
              setChangePasswordError(null);
            }}
            title="Change My Password"
            className="flex items-center gap-1 px-2 py-1 ml-1 rounded-md text-[11px] text-gray-500 hover:text-blue-600 hover:bg-blue-50 transition cursor-pointer"
          >
            <KeyRound className="w-3.5 h-3.5" />
            <span className="hidden xl:inline">Password</span>
          </button>

          <button
            onClick={() => setCurrentPage('login')}
            title="Sign Out / Switch Persona"
            className="flex items-center gap-1 px-2 py-1 ml-1 rounded-md text-[11px] text-gray-500 hover:text-red-600 hover:bg-red-50 transition cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span className="hidden xl:inline">Sign Out</span>
          </button>
        </div>
      </div>

      {/* Change Password Modal */}
      {isChangePasswordOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-sm overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
              <div className="flex items-center gap-2">
                <KeyRound className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">Change Account Password</h3>
              </div>
              <button
                onClick={() => setIsChangePasswordOpen(false)}
                className="text-slate-400 hover:text-slate-600 transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleChangePasswordSubmit} className="p-5 space-y-4">
              <div className="text-xs text-slate-500">
                Update your authoritative account credentials on the FastAPI authentication service.
              </div>

              {changePasswordError && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                  <span>{changePasswordError}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-800 mb-1.5">
                  Current Password <span className="text-rose-500">*</span>
                </label>
                <div className="relative">
                  <input
                    type={showOldPassword ? 'text' : 'password'}
                    value={oldPassword}
                    onChange={(e) => {
                      setOldPassword(e.target.value);
                      if (changePasswordError) setChangePasswordError(null);
                    }}
                    disabled={isChangingPassword}
                    placeholder="••••••••"
                    className="w-full bg-white border border-slate-200 rounded-lg pl-3 pr-10 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition disabled:bg-slate-50"
                    autoFocus
                  />
                  <button
                    type="button"
                    onClick={() => setShowOldPassword(!showOldPassword)}
                    disabled={isChangingPassword}
                    className="absolute right-3 top-2 text-slate-400 hover:text-slate-600 transition cursor-pointer"
                    title={showOldPassword ? 'Hide password' : 'Show password'}
                  >
                    {showOldPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-800 mb-1.5">
                  New Password <span className="text-rose-500">*</span> <span className="text-slate-400 font-normal">(min 8 chars)</span>
                </label>
                <div className="relative">
                  <input
                    type={showNewPassword ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => {
                      setNewPassword(e.target.value);
                      if (changePasswordError) setChangePasswordError(null);
                    }}
                    disabled={isChangingPassword}
                    placeholder="••••••••"
                    className="w-full bg-white border border-slate-200 rounded-lg pl-3 pr-10 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition disabled:bg-slate-50"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                    disabled={isChangingPassword}
                    className="absolute right-3 top-2 text-slate-400 hover:text-slate-600 transition cursor-pointer"
                    title={showNewPassword ? 'Hide password' : 'Show password'}
                  >
                    {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsChangePasswordOpen(false)}
                  disabled={isChangingPassword}
                  className="px-3.5 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 text-xs font-semibold transition cursor-pointer disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isChangingPassword}
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-xs font-semibold shadow-xs transition flex items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed"
                >
                  {isChangingPassword ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Saving...</span>
                    </>
                  ) : (
                    <span>Update Password</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </header>
  );
};
