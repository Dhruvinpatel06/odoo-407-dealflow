import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Sliders, 
  Settings, 
  DollarSign, 
  Percent, 
  Layers, 
  Bell, 
  Save, 
  RotateCcw,
  CheckCircle2,
  Building2,
  Warehouse,
  AlertTriangle
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { AccessRestrictedView } from '../common/AccessRestrictedView';

export const AdminConfigView: React.FC = () => {
  const { showNotification, currentUser } = useApp();

  // Defense-in-depth RBAC check
  if (currentUser.role !== 'ADMIN') {
    return (
      <AccessRestrictedView
        requiredRole="Platform Administrator (Alex Mercer)"
        featureName="System Governance & Policy Administration"
      />
    );
  }

  const [repCeiling, setRepCeiling] = useState(10);
  const [managerCeiling, setManagerCeiling] = useState(20);
  const [financeCeiling, setFinanceCeiling] = useState(35);
  const [minMarginFloor, setMinMarginFloor] = useState(30);
  const [riskWeightDiscount, setRiskWeightDiscount] = useState(40);
  const [riskWeightMargin, setRiskWeightMargin] = useState(35);
  const [riskWeightPayment, setRiskWeightPayment] = useState(25);

  const handleSavePolicy = (e: React.FormEvent) => {
    e.preventDefault();
    showNotification('Commercial governance policies committed to system configuration.', 'success');
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">System Governance & Policy Administration</h2>
          <p className="text-xs text-slate-500 mt-0.5">Authoritative discount ceilings, multi-level approval triggers, margin protection rules, and warehouse configurations.</p>
        </div>

        <button
          onClick={handleSavePolicy}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
        >
          <Save className="w-3.5 h-3.5" />
          <span>Save Governance Policies</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Policy Section 1: Discount Ceilings by Role (BR-01 / BR-02) */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <Percent className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-bold text-slate-900">Discount Ceilings by Role</h3>
          </div>

          <div className="space-y-3.5 text-xs">
            <div>
              <div className="flex justify-between font-semibold text-slate-700 mb-1">
                <span>Sales Representative Discretion:</span>
                <span className="font-mono font-bold text-blue-600">≤ {repCeiling}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="15"
                value={repCeiling}
                onChange={(e) => setRepCeiling(parseInt(e.target.value))}
                className="w-full accent-blue-600"
              />
              <span className="text-[11px] text-slate-400">Discounts at or below {repCeiling}% do not require approval unless margin floor breached.</span>
            </div>

            <div className="pt-2 border-t border-slate-100">
              <div className="flex justify-between font-semibold text-slate-700 mb-1">
                <span>Sales Manager Discretion Ceiling:</span>
                <span className="font-mono font-bold text-blue-600">≤ {managerCeiling}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="25"
                value={managerCeiling}
                onChange={(e) => setManagerCeiling(parseInt(e.target.value))}
                className="w-full accent-blue-600"
              />
              <span className="text-[11px] text-slate-400">Requires Single-Level (Manager) approval when exceeding {repCeiling}%.</span>
            </div>

            <div className="pt-2 border-t border-slate-100">
              <div className="flex justify-between font-semibold text-slate-700 mb-1">
                <span>Finance & RevOps Ceiling:</span>
                <span className="font-mono font-bold text-purple-600">&gt; {managerCeiling}% (Max {financeCeiling}%)</span>
              </div>
              <input
                type="range"
                min="20"
                max="50"
                value={financeCeiling}
                onChange={(e) => setFinanceCeiling(parseInt(e.target.value))}
                className="w-full accent-purple-600"
              />
              <span className="text-[11px] text-slate-400">Triggers sequential two-tier approval (Manager → Finance) automatically.</span>
            </div>
          </div>
        </div>

        {/* Policy Section 2: Margin Protection Floors (BR-03 / BR-04) */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <h3 className="text-sm font-bold text-slate-900">Corporate Margin Protection</h3>
          </div>

          <div className="space-y-3.5 text-xs">
            <div>
              <div className="flex justify-between font-semibold text-slate-700 mb-1">
                <span>Minimum Corporate Margin Floor:</span>
                <span className="font-mono font-bold text-emerald-600">{minMarginFloor}%</span>
              </div>
              <input
                type="range"
                min="20"
                max="40"
                value={minMarginFloor}
                onChange={(e) => setMinMarginFloor(parseInt(e.target.value))}
                className="w-full accent-emerald-600"
              />
              <span className="text-[11px] text-slate-400">Any line item or blended deal falling below {minMarginFloor}% margin triggers mandatory Finance sign-off.</span>
            </div>

            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs">
              <span className="font-bold block mb-1">Hard Floor Violation Policy:</span>
              Quotes with margin &lt; 20% are flagged as CRITICAL risk and require executive justification notes before submission.
            </div>

            <div className="space-y-2 pt-2 border-t border-slate-100">
              <span className="font-bold text-slate-700 block">Category Base Margin Standards:</span>
              <div className="flex justify-between text-slate-600">
                <span>Hardware Components:</span>
                <span className="font-mono font-semibold">25.0% min</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Software Subscriptions:</span>
                <span className="font-mono font-semibold">60.0% min</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Professional Services:</span>
                <span className="font-mono font-semibold">35.0% min</span>
              </div>
            </div>
          </div>
        </div>

        {/* Policy Section 3: Risk Scoring Weights (AI / Governance Engine) */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <Sliders className="w-4 h-4 text-purple-600" />
            <h3 className="text-sm font-bold text-slate-900">Governance Risk Weights</h3>
          </div>

          <div className="space-y-3.5 text-xs">
            <div>
              <div className="flex justify-between font-semibold text-slate-700 mb-1">
                <span>Discount Breach Weight:</span>
                <span className="font-mono font-bold text-purple-600">{riskWeightDiscount}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="60"
                value={riskWeightDiscount}
                onChange={(e) => setRiskWeightDiscount(parseInt(e.target.value))}
                className="w-full accent-purple-600"
              />
            </div>

            <div>
              <div className="flex justify-between font-semibold text-slate-700 mb-1">
                <span>Margin Deviation Weight:</span>
                <span className="font-mono font-bold text-purple-600">{riskWeightMargin}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="60"
                value={riskWeightMargin}
                onChange={(e) => setRiskWeightMargin(parseInt(e.target.value))}
                className="w-full accent-purple-600"
              />
            </div>

            <div>
              <div className="flex justify-between font-semibold text-slate-700 mb-1">
                <span>Payment Terms Sensitivity:</span>
                <span className="font-mono font-bold text-purple-600">{riskWeightPayment}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="50"
                value={riskWeightPayment}
                onChange={(e) => setRiskWeightPayment(parseInt(e.target.value))}
                className="w-full accent-purple-600"
              />
            </div>

            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-slate-600 text-[11px] leading-relaxed">
              Risk score scale: <strong className="text-emerald-700">0-30 Healthy</strong>, <strong className="text-amber-700">31-60 Moderate</strong>, <strong className="text-rose-700">&gt;60 High Risk</strong>.
            </div>
          </div>
        </div>
      </div>

      {/* Warehouses & Logistics Hubs Configuration */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Warehouse className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-bold text-slate-900">Active Warehouses & Distribution Hubs</h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">2 Configured Centers</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-2">
            <div className="flex justify-between items-center">
              <strong className="text-slate-900 text-sm">Main Distribution Center (ORD-MAIN)</strong>
              <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold text-[10px]">Active Hub</span>
            </div>
            <p className="text-slate-500">Location: Chicago, IL • Freight Cost Weight: 1.0x (Standard)</p>
            <div className="text-[11px] text-slate-600 font-mono">Capacity: 45,000 sq ft • Lead Time: 2 Business Days</div>
          </div>

          <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-2">
            <div className="flex justify-between items-center">
              <strong className="text-slate-900 text-sm">East Coast Depot (EWR-DEPOT)</strong>
              <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold text-[10px]">Active Hub</span>
            </div>
            <p className="text-slate-500">Location: Newark, NJ • Freight Cost Weight: 1.3x</p>
            <div className="text-[11px] text-slate-600 font-mono">Capacity: 22,000 sq ft • Lead Time: 3 Business Days</div>
          </div>
        </div>
      </div>
    </div>
  );
};
