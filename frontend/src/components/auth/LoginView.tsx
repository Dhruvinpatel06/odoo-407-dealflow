import React from 'react';
import { 
  Shield, 
  UserCheck, 
  Briefcase, 
  DollarSign, 
  Truck, 
  Users, 
  ShieldAlert, 
  ArrowRight,
  Sparkles,
  CheckCircle2
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { UserRole } from '../../types';

export const LoginView: React.FC = () => {
  const { userRole, setUserRole, setCurrentPage, showNotification } = useApp();

  const personas: {
    role: UserRole;
    name: string;
    title: string;
    description: string;
    icon: any;
    targetPage: any;
    color: string;
    badge: string;
  }[] = [
    {
      role: 'SALES_REP',
      name: 'Sarah Chen',
      title: 'Senior Account Executive',
      description: 'Creates quotes, adds products, adjusts discounts up to 10%, submits for backend evaluation.',
      icon: Briefcase,
      targetPage: 'quote-builder',
      color: 'border-blue-200 hover:border-blue-500 bg-blue-50/30',
      badge: 'Discounts ≤ 10%'
    },
    {
      role: 'SALES_MANAGER',
      name: 'David Miller',
      title: 'Commercial Sales Director',
      description: 'Reviews pending approvals, approves or returns deals for revision up to 20% discount.',
      icon: UserCheck,
      targetPage: 'approvals',
      color: 'border-indigo-200 hover:border-indigo-500 bg-indigo-50/30',
      badge: 'Level 1 Approver'
    },
    {
      role: 'FINANCE_OPERATIONS',
      name: 'Elena Rostova',
      title: 'VP of Finance & RevOps',
      description: 'Reviews margin breaches, discount ceilings > 20%, multi-tier approval chains and contracts.',
      icon: DollarSign,
      targetPage: 'approvals',
      color: 'border-purple-200 hover:border-purple-500 bg-purple-50/30',
      badge: 'Level 2 Approver'
    },
    {
      role: 'FULFILLMENT_OPERATOR',
      name: 'Carlos Ruiz',
      title: 'Logistics & Warehouse Lead',
      description: 'Inspects split warehouse allocations, resolves backorders, consolidates multi-hub freight.',
      icon: Truck,
      targetPage: 'fulfillment',
      color: 'border-amber-200 hover:border-amber-500 bg-amber-50/30',
      badge: 'Warehouse Routing'
    },
    {
      role: 'CUSTOMER_PORTAL',
      name: 'Rachel Adams',
      title: 'VP Technology, Acme Corp',
      description: 'Customer viewpoint. Zero internal risk/margins shown. Propose counter-discounts or accept.',
      icon: Users,
      targetPage: 'customer-portal',
      color: 'border-emerald-200 hover:border-emerald-500 bg-emerald-50/30',
      badge: 'External Portal'
    },
    {
      role: 'ADMIN',
      name: 'System Admin',
      title: 'Platform Governance Admin',
      description: 'Configures corporate margin floors, discount ceilings by role, and warehouse weights.',
      icon: Shield,
      targetPage: 'admin-config',
      color: 'border-slate-300 hover:border-slate-600 bg-slate-50',
      badge: 'Policy Governance'
    }
  ];

  const handleSelectRole = (p: typeof personas[0]) => {
    setUserRole(p.role);
    setCurrentPage(p.targetPage);
    showNotification(`Switched persona to ${p.name} (${p.title}).`, 'info');
  };

  return (
    <div className="min-h-[85vh] flex flex-col items-center justify-center p-6 max-w-5xl mx-auto space-y-6">
      <div className="text-center space-y-2 max-w-lg">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Hackathon Evaluation Persona Switcher</span>
        </div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Select User Persona to Enter</h1>
        <p className="text-xs text-slate-500 leading-relaxed">
          DealFlow360 dynamically adapts views, permissions, approval authority, and telemetry access based on active role identity.
        </p>
      </div>

      {/* Grid of Personas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 w-full">
        {personas.map((p) => {
          const isCurrent = userRole === p.role;
          const Icon = p.icon;

          return (
            <div
              key={p.role}
              onClick={() => handleSelectRole(p)}
              className={`p-5 rounded-xl border transition-all cursor-pointer shadow-xs hover:shadow-md flex flex-col justify-between ${p.color} ${
                isCurrent ? 'ring-2 ring-blue-600 border-blue-600 bg-white' : ''
              }`}
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="w-9 h-9 rounded-lg bg-white shadow-2xs border border-slate-200 flex items-center justify-center text-slate-800">
                    <Icon className="w-5 h-5 text-blue-600" />
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-700">
                    {p.badge}
                  </span>
                </div>

                <div>
                  <h3 className="text-sm font-bold text-slate-900">{p.name}</h3>
                  <div className="text-xs font-semibold text-slate-500">{p.title}</div>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed">
                  {p.description}
                </p>
              </div>

              <div className="pt-4 mt-2 border-t border-slate-200/60 flex items-center justify-between text-xs font-semibold text-blue-600">
                <span>Launch Persona</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
