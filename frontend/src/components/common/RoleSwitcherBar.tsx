import React from 'react';
import { useApp } from '../../context/AppContext';
import { UserRole } from '../../types';
import { getRoleMeta } from '../../utils/rbac';
import { Shield, ShieldAlert, Sparkles, User, Info, ArrowRight } from 'lucide-react';

export const RoleSwitcherBar: React.FC = () => {
  const { currentUser, setUserRole, setCurrentPage } = useApp();
  const currentRole = currentUser.role;
  const meta = getRoleMeta(currentRole);

  const roles: { role: UserRole; label: string; user: string }[] = [
    { role: 'SALES_REP', label: 'Sales Rep', user: 'Sarah Chen' },
    { role: 'SALES_MANAGER', label: 'Sales Manager', user: 'Marcus Vance' },
    { role: 'FINANCE_OPERATIONS', label: 'Finance & Ops', user: 'Elena Rostova' },
    { role: 'ADMIN', label: 'Admin', user: 'Alex Mercer' },
    { role: 'CUSTOMER_PORTAL', label: 'Customer Portal', user: 'David Kross' }
  ];

  return (
    <div className="bg-white border-b border-gray-200 px-8 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs">
      {/* Active Persona Info */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 font-semibold text-gray-700">
          <Shield className="w-3.5 h-3.5 text-[#2563EB]" />
          <span className="text-gray-500 font-normal">Active RBAC Persona:</span>
        </div>

        <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold border ${meta.badgeColor}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${meta.badgeDot}`}></span>
          <span>{meta.label}</span>
          <span className="font-normal opacity-80">({meta.name})</span>
        </span>

        <span className="hidden xl:inline-block text-gray-500 border-l border-gray-200 pl-3">
          {meta.restrictionsSummary}
        </span>
      </div>

      {/* Quick 1-Click Role Switcher Pills */}
      <div className="flex items-center gap-1.5">
        <span className="text-[11px] font-medium text-gray-400 mr-1 hidden sm:inline">Simulate Role:</span>
        <div className="inline-flex bg-gray-100 p-0.5 rounded-lg border border-gray-200">
          {roles.map((r) => {
            const isSelected = r.role === currentRole;
            return (
              <button
                key={r.role}
                onClick={() => {
                  setUserRole(r.role);
                }}
                className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-white text-gray-900 shadow-xs'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-200/50'
                }`}
                title={`Switch to ${r.label} (${r.user})`}
              >
                {r.label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
