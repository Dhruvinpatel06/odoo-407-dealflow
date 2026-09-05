import React from 'react';
import { 
  LayoutDashboard, 
  FileText, 
  CheckCircle2, 
  Truck, 
  CreditCard, 
  Activity, 
  BarChart3, 
  Settings, 
  ShieldCheck, 
  ExternalLink,
  ChevronRight,
  Sparkles,
  Users
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { UserRole } from '../../types';
import { getRoleNavItems, getRoleMeta } from '../../utils/rbac';

export const Sidebar: React.FC = () => {
  const { 
    currentPage, 
    setCurrentPage, 
    currentUser, 
    setUserRole, 
    approvals, 
    dealAlerts,
    setIsGuideOpen 
  } = useApp();

  const pendingApprovalsCount = approvals.filter(a => a.status === 'PENDING').length;
  const activeAlertsCount = dealAlerts.filter(a => a.status === 'OPEN').length;

  const navItems = getRoleNavItems(currentUser.role, pendingApprovalsCount, activeAlertsCount);
  const roleMeta = getRoleMeta(currentUser.role);

  return (
    <aside className="w-[240px] bg-white border-r border-gray-200 flex flex-col h-screen shrink-0 select-none">
      {/* Brand Header matching Editorial Aesthetic */}
      <div className="p-6 pb-4 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-[#2563EB] rounded-lg flex items-center justify-center shadow-xs">
            <div className="w-4 h-4 border-2 border-white rotate-45"></div>
          </div>
          <div>
            <span className="font-bold text-xl tracking-tight text-[#111827]">
              DealFlow<span className="text-[#2563EB]">360</span>
            </span>
          </div>
        </div>
      </div>

      {/* Role Pill Indicator in Sidebar */}
      <div className="px-5 pb-3">
        <div className={`p-2 rounded-lg border text-[11px] flex items-center justify-between ${roleMeta.badgeColor}`}>
          <div className="flex items-center gap-1.5 font-bold truncate">
            <span className={`w-2 h-2 rounded-full shrink-0 ${roleMeta.badgeDot}`}></span>
            <span className="truncate">{roleMeta.label}</span>
          </div>
          <span className="text-[10px] font-mono opacity-80 shrink-0">RBAC</span>
        </div>
      </div>

      {/* Quick Test Guide Trigger Banner */}
      <div className="px-4 pb-2">
        <button
          onClick={() => setIsGuideOpen(true)}
          className="w-full flex items-center justify-between px-3 py-2 rounded-md bg-blue-50/70 hover:bg-blue-100/80 border border-blue-200 text-[#2563EB] text-xs font-semibold transition group shadow-2xs cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-[#2563EB] animate-pulse" />
            <span>Acceptance Test (1-8)</span>
          </div>
          <ChevronRight className="w-3.5 h-3.5 text-[#2563EB] group-hover:translate-x-0.5 transition-transform" />
        </button>
      </div>

      {/* Primary Navigation */}
      <nav className="flex-1 px-4 py-2 space-y-1 overflow-y-auto">
        <div className="px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
          Core Operations
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          const isHighlighted = item.highlighted;

          return (
            <button
              key={item.id}
              onClick={() => setCurrentPage(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-xs transition-colors cursor-pointer ${
                isActive
                  ? isHighlighted
                    ? 'bg-purple-600 text-white font-bold shadow-xs'
                    : 'bg-blue-50 text-[#2563EB] font-medium'
                  : isHighlighted
                  ? 'bg-purple-50/80 border border-purple-200/90 text-purple-900 font-bold hover:bg-purple-100/80'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 font-medium'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${
                  isActive 
                    ? isHighlighted ? 'text-white' : 'text-[#2563EB]' 
                    : isHighlighted ? 'text-purple-600' : 'text-gray-500'
                }`} />
                <span>{item.label}</span>
              </div>
              {item.alertBadge && (
                <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                  isHighlighted && !isActive
                    ? 'bg-purple-600 text-white animate-pulse'
                    : isActive && isHighlighted
                    ? 'bg-white text-purple-700'
                    : 'bg-rose-500 text-white'
                }`}>
                  {item.alertBadge}
                </span>
              )}
              {item.badge && !item.alertBadge && (
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${isActive ? 'bg-blue-100 text-[#2563EB]' : 'bg-gray-100 text-gray-500'}`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}

        {/* Customer Portal Link */}
        <div className="pt-4 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
          External Experience
        </div>
        <button
          onClick={() => {
            setUserRole('CUSTOMER_PORTAL');
          }}
          className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-xs font-medium transition cursor-pointer border ${
            currentPage === 'portal'
              ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
              : 'text-gray-600 border-gray-200 hover:bg-gray-50 hover:text-gray-900'
          }`}
        >
          <div className="flex items-center gap-3">
            <ExternalLink className="w-4 h-4 text-emerald-600" />
            <span className="font-semibold text-emerald-700">Customer Portal</span>
          </div>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700 border border-emerald-200 font-mono">
            Client
          </span>
        </button>
      </nav>

      {/* Role Switcher & Persona Bar matching Editorial Aesthetic */}
      <div className="p-4 border-t border-gray-100">
        <div className="flex items-center justify-between mb-2 px-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400 flex items-center gap-1">
            <Users className="w-3 h-3 text-gray-400" /> Role Persona
          </span>
          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-gray-100 text-[#2563EB] font-medium">
            FastAPI Mock
          </span>
        </div>

        {/* Quick Persona Switcher */}
        <select
          value={currentUser.role}
          onChange={(e) => setUserRole(e.target.value as UserRole)}
          className="w-full bg-gray-50 hover:bg-white border border-gray-200 text-xs text-gray-800 rounded-md p-1.5 focus:outline-hidden focus:ring-2 focus:ring-blue-500 font-medium cursor-pointer transition"
        >
          <option value="SALES_REP">Sales Rep (Sarah Chen)</option>
          <option value="SALES_MANAGER">Sales Manager (Marcus Vance)</option>
          <option value="FINANCE_OPERATIONS">Finance / Ops (Elena Rostova)</option>
          <option value="FULFILLMENT_OPERATOR">Fulfillment (Carlos Ruiz)</option>
          <option value="CUSTOMER_PORTAL">Customer (David Kross)</option>
          <option value="ADMIN">Platform Admin (Alex Mercer)</option>
        </select>

        {/* Current User Card */}
        <div className="mt-3 flex items-center gap-3 p-2 bg-gray-50 rounded-lg border border-gray-100">
          <img
            src={currentUser.avatar}
            alt={currentUser.name}
            className="w-8 h-8 rounded-full object-cover border border-gray-200 shrink-0"
          />
          <div className="min-w-0 flex-1">
            <p className="text-xs font-bold truncate text-[#111827]">{currentUser.name}</p>
            <p className="text-[10px] text-gray-500 uppercase tracking-wider truncate">{currentUser.title}</p>
          </div>
          <button 
            onClick={() => setCurrentPage('login')}
            title="Log out or switch account"
            className="text-gray-400 hover:text-gray-700 p-1 rounded hover:bg-gray-200/60 transition cursor-pointer"
          >
            <Settings className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );
};
