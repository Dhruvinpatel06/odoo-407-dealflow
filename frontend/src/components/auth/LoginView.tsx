import React, { useState } from 'react';
import { 
  Mail, 
  Lock, 
  Eye, 
  EyeOff, 
  ChevronDown, 
  ArrowRight 
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { UserRole } from '../../types';

interface RoleOption {
  role: UserRole;
  label: string;
  name: string;
  email: string;
  pass: string;
  targetPage: string;
}

const ROLE_OPTIONS: RoleOption[] = [
  {
    role: 'SALES_REP',
    label: 'Sales Representative (Sarah Chen)',
    name: 'Sarah Chen',
    email: 'sales@dealflow360.io',
    pass: 'sales123',
    targetPage: 'dashboard'
  },
  {
    role: 'SALES_MANAGER',
    label: 'Sales Manager (Marcus Vance)',
    name: 'Marcus Vance',
    email: 'manager@dealflow360.io',
    pass: 'manager123',
    targetPage: 'approvals'
  },
  {
    role: 'FINANCE_OPERATIONS',
    label: 'Finance & Operations (Elena Rostova)',
    name: 'Elena Rostova',
    email: 'finance@dealflow360.io',
    pass: 'finance123',
    targetPage: 'billing'
  },
  {
    role: 'CUSTOMER_PORTAL',
    label: 'Customer Portal (David Kross - Acme Corp)',
    name: 'David Kross',
    email: 'david.kross@acmecorp.com',
    pass: 'customer123',
    targetPage: 'portal'
  },
  {
    role: 'ADMIN',
    label: 'Platform Administrator (Alex Mercer)',
    name: 'Alex Mercer',
    email: 'admin@dealflow360.io',
    pass: 'admin123',
    targetPage: 'admin-config'
  }
];

export const LoginView: React.FC = () => {
  const { setUserRole, setCurrentPage, showNotification } = useApp();
  
  const [selectedRole, setSelectedRole] = useState<string>('');
  const [emailInput, setEmailInput] = useState<string>('');
  const [passwordInput, setPasswordInput] = useState<string>('');
  const [showPassword, setShowPassword] = useState<boolean>(false);

  const handleRoleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const roleKey = e.target.value;
    setSelectedRole(roleKey);

    const matched = ROLE_OPTIONS.find(r => r.role === roleKey);
    if (matched) {
      setEmailInput(matched.email);
      setPasswordInput(matched.pass);
    }
  };

  const handleSignIn = (e: React.FormEvent) => {
    e.preventDefault();

    let matched = ROLE_OPTIONS.find(r => r.role === selectedRole);

    if (!matched && emailInput.trim()) {
      matched = ROLE_OPTIONS.find(
        r => r.email.toLowerCase() === emailInput.trim().toLowerCase()
      );
    }

    if (!matched) {
      matched = ROLE_OPTIONS[0]; // Default to Sales Rep for smooth demo experience
    }

    setUserRole(matched.role);
    setCurrentPage(matched.targetPage);
    showNotification(`Signed in as ${matched.name} (${matched.label.split('(')[0].trim()})`, 'success');
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col items-center justify-center p-4 select-none">
      {/* Brand Header */}
      <div className="flex flex-col items-center text-center mb-6">
        <div className="w-12 h-12 bg-[#2563EB] rounded-2xl flex items-center justify-center shadow-xs mb-3.5">
          <div className="w-4 h-4 border-2 border-white rotate-45 rounded-2xs"></div>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">
          DealFlow<span className="text-[#2563EB]">360</span>
        </h1>
        <p className="text-xs text-slate-500 font-normal mt-1">
          Intelligent Sales Operations Platform
        </p>
      </div>

      {/* Auth Card */}
      <div className="w-full max-w-[430px] bg-white rounded-2xl border border-slate-200/80 shadow-xs p-8">
        <form onSubmit={handleSignIn} className="space-y-4">
          {/* Role Field */}
          <div>
            <label className="block text-xs font-semibold text-slate-800 mb-1.5">
              Role
            </label>
            <div className="relative">
              <select
                value={selectedRole}
                onChange={handleRoleChange}
                className="w-full appearance-none bg-white border border-slate-200 rounded-lg px-3.5 py-2.5 text-xs text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition cursor-pointer pr-10"
              >
                <option value="" disabled>
                  Select Role
                </option>
                {ROLE_OPTIONS.map((opt) => (
                  <option key={opt.role} value={opt.role}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3.5 top-3 pointer-events-none" />
            </div>
            <p className="text-[11px] text-slate-400 mt-1.5">
              Demo mode &mdash; select a role to continue
            </p>
          </div>

          {/* Email Field */}
          <div>
            <label className="block text-xs font-semibold text-slate-800 mb-1.5">
              Email
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3 pointer-events-none" />
              <input
                type="email"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                placeholder="name@dealflow360.io"
                className="w-full bg-white border border-slate-200 rounded-lg pl-10 pr-3.5 py-2.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition"
              />
            </div>
          </div>

          {/* Password Field */}
          <div>
            <label className="block text-xs font-semibold text-slate-800 mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3 pointer-events-none" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;"
                className="w-full bg-white border border-slate-200 rounded-lg pl-10 pr-10 py-2.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 transition p-0.5 cursor-pointer"
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? (
                  <EyeOff className="w-4 h-4" />
                ) : (
                  <Eye className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* Submit Button */}
          <div className="pt-2">
            <button
              type="submit"
              className="w-full py-2.5 px-4 bg-[#2563EB] hover:bg-blue-700 text-white font-semibold text-xs rounded-lg flex items-center justify-center gap-2 transition-colors shadow-xs cursor-pointer"
            >
              <span>Sign In to DealFlow360</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
