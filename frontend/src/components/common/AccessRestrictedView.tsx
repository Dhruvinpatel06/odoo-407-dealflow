import React from 'react';
import { ShieldAlert, ArrowLeft, KeyRound, CheckCircle2 } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { getRoleMeta } from '../../utils/rbac';

interface AccessRestrictedViewProps {
  requiredRole?: string;
  featureName?: string;
}

export const AccessRestrictedView: React.FC<AccessRestrictedViewProps> = ({
  requiredRole = 'Platform Administrator (Alex Mercer)',
  featureName = 'System Administration & Configuration'
}) => {
  const { currentUser, setUserRole, setCurrentPage } = useApp();
  const meta = getRoleMeta(currentUser.role);

  return (
    <div className="min-h-[70vh] flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-2xl border border-gray-200 p-8 shadow-sm text-center">
        <div className="w-14 h-14 rounded-2xl bg-amber-50 text-amber-600 border border-amber-200 flex items-center justify-center mx-auto mb-5 shadow-xs">
          <ShieldAlert className="w-7 h-7" />
        </div>

        <span className="text-[10px] font-mono font-bold tracking-wider uppercase text-amber-700 bg-amber-100/70 px-2.5 py-1 rounded-full border border-amber-200">
          RBAC Governance Enforced
        </span>

        <h3 className="text-xl font-bold text-gray-900 tracking-tight mt-3">
          Access Restricted
        </h3>

        <p className="text-xs text-gray-500 mt-2 leading-relaxed">
          {featureName} is not accessible for your current role: <strong className="text-gray-800">{meta.label}</strong> ({currentUser.name}).
        </p>

        <div className="my-6 p-4 rounded-xl bg-gray-50 border border-gray-200 text-left text-xs space-y-2">
          <div className="flex items-center justify-between text-gray-500 text-[11px]">
            <span>Required Role:</span>
            <span className="font-semibold text-gray-900">{requiredRole}</span>
          </div>
          <div className="flex items-center justify-between text-gray-500 text-[11px]">
            <span>Your Active Persona:</span>
            <span className={`font-semibold px-2 py-0.5 rounded border ${meta.badgeColor}`}>
              {meta.label}
            </span>
          </div>
          <p className="text-[11px] text-gray-400 pt-1 border-t border-gray-200">
            In production, DealFlow360 hides unauthorized routes from navigation menus and rejects unauthorized API requests with HTTP 403 Forbidden.
          </p>
        </div>

        <div className="space-y-2.5">
          <button
            onClick={() => {
              setUserRole('ADMIN');
              setCurrentPage('admin');
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
          >
            <KeyRound className="w-4 h-4" />
            <span>Switch to Platform Admin Persona</span>
          </button>

          <button
            onClick={() => setCurrentPage('dashboard')}
            className="w-full flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 text-gray-700 text-xs font-medium transition cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Dashboard</span>
          </button>
        </div>
      </div>
    </div>
  );
};
