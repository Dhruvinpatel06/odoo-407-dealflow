import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Sliders, 
  Percent, 
  Save, 
  Package,
  Warehouse as WarehouseIcon,
  Repeat,
  DollarSign,
  Boxes
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { AccessRestrictedView } from '../common/AccessRestrictedView';
import { mockProducts, mockWarehouses } from '../../mockData';

export const AdminConfigView: React.FC = () => {
  const { showNotification, currentUser, governanceConfig, updateGovernanceConfig, subscriptions } = useApp();

  // Defense-in-depth RBAC check
  if (currentUser.role !== 'ADMIN') {
    return (
      <AccessRestrictedView
        requiredRole="Platform Administrator (Alex Mercer)"
        featureName="System Governance & Policy Administration"
      />
    );
  }

  const [activeTab, setActiveTab] = useState<'DISCOUNTS' | 'CATALOG' | 'WAREHOUSES' | 'SUBSCRIPTIONS' | 'RISK'>('DISCOUNTS');

  // Local state initialized from canonical governanceConfig
  const [repCeiling, setRepCeiling] = useState(governanceConfig.roleCeilings.repCeiling);
  const [managerCeiling, setManagerCeiling] = useState(governanceConfig.roleCeilings.managerCeiling);
  const [financeCeiling, setFinanceCeiling] = useState(governanceConfig.roleCeilings.financeCeiling);
  const [minMarginFloor, setMinMarginFloor] = useState(governanceConfig.minCorporateMarginFloor);
  
  const [tierPlatinum, setTierPlatinum] = useState(governanceConfig.tierDiscountCeilings.PLATINUM);
  const [tierGold, setTierGold] = useState(governanceConfig.tierDiscountCeilings.GOLD);
  const [tierSilver, setTierSilver] = useState(governanceConfig.tierDiscountCeilings.SILVER);
  const [tierBronze, setTierBronze] = useState(governanceConfig.tierDiscountCeilings.BRONZE);

  const [catHardware, setCatHardware] = useState(governanceConfig.categoryDiscountCeilings.HARDWARE);
  const [catSubscription, setCatSubscription] = useState(governanceConfig.categoryDiscountCeilings.SUBSCRIPTION);
  const [catServices, setCatServices] = useState(governanceConfig.categoryDiscountCeilings.SERVICES);

  const [riskThresholdManager, setRiskThresholdManager] = useState(governanceConfig.managerApprovalRiskThreshold);
  const [riskThresholdFinance, setRiskThresholdFinance] = useState(governanceConfig.financeApprovalRiskThreshold);

  const [riskWeightDiscount, setRiskWeightDiscount] = useState(governanceConfig.riskWeights.discountBreach);
  const [riskWeightMargin, setRiskWeightMargin] = useState(governanceConfig.riskWeights.marginDeviation);
  const [riskWeightPayment, setRiskWeightPayment] = useState(governanceConfig.riskWeights.paymentRisk);

  const handleSavePolicy = (e: React.FormEvent) => {
    e.preventDefault();
    updateGovernanceConfig({
      roleCeilings: {
        repCeiling,
        managerCeiling,
        financeCeiling
      },
      minCorporateMarginFloor: minMarginFloor,
      tierDiscountCeilings: {
        PLATINUM: tierPlatinum,
        GOLD: tierGold,
        SILVER: tierSilver,
        BRONZE: tierBronze
      },
      categoryDiscountCeilings: {
        HARDWARE: catHardware,
        SUBSCRIPTION: catSubscription,
        SERVICES: catServices
      },
      managerApprovalRiskThreshold: riskThresholdManager,
      financeApprovalRiskThreshold: riskThresholdFinance,
      riskWeights: {
        discountBreach: riskWeightDiscount,
        marginDeviation: riskWeightMargin,
        paymentRisk: riskWeightPayment
      }
    });
    showNotification('Commercial governance policies committed to system configuration.', 'success');
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">System Governance & Policy Administration</h2>
          <p className="text-xs text-slate-500 mt-0.5">Authoritative discount ceilings, multi-level approval triggers, catalog controls, and warehouse configurations.</p>
        </div>

        <button
          onClick={handleSavePolicy}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
        >
          <Save className="w-3.5 h-3.5" />
          <span>Save Governance Policies</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 overflow-x-auto gap-2">
        <button
          onClick={() => setActiveTab('DISCOUNTS')}
          className={`pb-3 px-3 text-xs font-bold border-b-2 transition flex items-center gap-2 cursor-pointer ${
            activeTab === 'DISCOUNTS' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Percent className="w-3.5 h-3.5" />
          <span>1. Discount Ceilings</span>
        </button>

        <button
          onClick={() => setActiveTab('CATALOG')}
          className={`pb-3 px-3 text-xs font-bold border-b-2 transition flex items-center gap-2 cursor-pointer ${
            activeTab === 'CATALOG' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Package className="w-3.5 h-3.5" />
          <span>2. Catalog & Price Lists</span>
        </button>

        <button
          onClick={() => setActiveTab('WAREHOUSES')}
          className={`pb-3 px-3 text-xs font-bold border-b-2 transition flex items-center gap-2 cursor-pointer ${
            activeTab === 'WAREHOUSES' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <WarehouseIcon className="w-3.5 h-3.5" />
          <span>3. Warehouses & Stock</span>
        </button>

        <button
          onClick={() => setActiveTab('SUBSCRIPTIONS')}
          className={`pb-3 px-3 text-xs font-bold border-b-2 transition flex items-center gap-2 cursor-pointer ${
            activeTab === 'SUBSCRIPTIONS' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Repeat className="w-3.5 h-3.5" />
          <span>4. Subscriptions & Billing</span>
        </button>

        <button
          onClick={() => setActiveTab('RISK')}
          className={`pb-3 px-3 text-xs font-bold border-b-2 transition flex items-center gap-2 cursor-pointer ${
            activeTab === 'RISK' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>5. Risk Scoring & Margin</span>
        </button>
      </div>

      {/* Tab 1: Discount Ceilings */}
      {activeTab === 'DISCOUNTS' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Ceilings by Role */}
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
                  <span>Sales Manager Discretion:</span>
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

          {/* Customer Tier Ceilings */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
              <ShieldCheck className="w-4 h-4 text-amber-600" />
              <h3 className="text-sm font-bold text-slate-900">Customer Tier Ceilings</h3>
            </div>

            <div className="space-y-3.5 text-xs">
              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Platinum Tier Ceiling:</span>
                  <span className="font-mono font-bold text-amber-600">{tierPlatinum}%</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="35"
                  value={tierPlatinum}
                  onChange={(e) => setTierPlatinum(parseInt(e.target.value))}
                  className="w-full accent-amber-600"
                />
              </div>

              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Gold Tier Ceiling:</span>
                  <span className="font-mono font-bold text-amber-600">{tierGold}%</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="25"
                  value={tierGold}
                  onChange={(e) => setTierGold(parseInt(e.target.value))}
                  className="w-full accent-amber-600"
                />
              </div>

              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Silver Tier Ceiling:</span>
                  <span className="font-mono font-bold text-amber-600">{tierSilver}%</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="20"
                  value={tierSilver}
                  onChange={(e) => setTierSilver(parseInt(e.target.value))}
                  className="w-full accent-amber-600"
                />
              </div>

              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Bronze Tier Ceiling:</span>
                  <span className="font-mono font-bold text-amber-600">{tierBronze}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="15"
                  value={tierBronze}
                  onChange={(e) => setTierBronze(parseInt(e.target.value))}
                  className="w-full accent-amber-600"
                />
              </div>
            </div>
          </div>

          {/* Product Category Ceilings */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
              <Sliders className="w-4 h-4 text-emerald-600" />
              <h3 className="text-sm font-bold text-slate-900">Product Category Ceilings</h3>
            </div>

            <div className="space-y-3.5 text-xs">
              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Hardware Products:</span>
                  <span className="font-mono font-bold text-emerald-600">{catHardware}% max</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="30"
                  value={catHardware}
                  onChange={(e) => setCatHardware(parseInt(e.target.value))}
                  className="w-full accent-emerald-600"
                />
              </div>

              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Subscription Software:</span>
                  <span className="font-mono font-bold text-emerald-600">{catSubscription}% max</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="40"
                  value={catSubscription}
                  onChange={(e) => setCatSubscription(parseInt(e.target.value))}
                  className="w-full accent-emerald-600"
                />
              </div>

              <div>
                <div className="flex justify-between font-semibold text-slate-700 mb-1">
                  <span>Professional Services:</span>
                  <span className="font-mono font-bold text-emerald-600">{catServices}% max</span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="25"
                  value={catServices}
                  onChange={(e) => setCatServices(parseInt(e.target.value))}
                  className="w-full accent-emerald-600"
                />
              </div>

              <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs">
                Authoritative Rule: Lowest ceiling applies between Customer Tier and Category (BR-02).
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Catalog & Price Lists */}
      {activeTab === 'CATALOG' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900">Configured Products & Pricing Tiers</h3>
            <span className="text-xs text-slate-400 font-mono">{mockProducts.length} Active SKUs</span>
          </div>
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[10px]">
                <th className="py-3 px-4">SKU / Product</th>
                <th className="py-3 px-3">Category</th>
                <th className="py-3 px-3">List Price</th>
                <th className="py-3 px-3">Unit Cost</th>
                <th className="py-3 px-3">Gross Margin</th>
                <th className="py-3 px-3">Discount Limit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {mockProducts.map((p) => {
                const margin = (((p.unitPrice - p.unitCost) / p.unitPrice) * 100).toFixed(1);
                return (
                  <tr key={p.id} className="hover:bg-slate-50/60">
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">{p.name}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{p.sku}</div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">
                        {p.category}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono font-bold text-slate-900">${p.unitPrice.toLocaleString()}</td>
                    <td className="py-3 px-3 font-mono text-slate-600">${p.unitCost.toLocaleString()}</td>
                    <td className="py-3 px-3 font-mono font-semibold text-emerald-600">{margin}%</td>
                    <td className="py-3 px-3 font-mono font-semibold text-blue-600">{p.categoryDiscountCeiling}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 3: Warehouses & Stock */}
      {activeTab === 'WAREHOUSES' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {mockWarehouses.map((wh) => (
            <div key={wh.id} className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
              <div className="flex justify-between items-center pb-2 border-b border-slate-100">
                <strong className="text-slate-900 text-sm">{wh.name}</strong>
                <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold text-[10px]">{wh.code}</span>
              </div>
              <p className="text-xs text-slate-500">Location: {wh.city} &bull; Freight Factor: {wh.shippingWeight}x</p>
              <div className="text-xs space-y-1.5 pt-2">
                <span className="font-bold text-slate-700 block">Inventory Levels:</span>
                {Object.entries(wh.stockByProduct).map(([pid, qty]) => (
                  <div key={pid} className="flex justify-between text-slate-600 font-mono text-[11px]">
                    <span>{pid.toUpperCase()}:</span>
                    <span className="font-bold text-blue-700">{qty} units in stock</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab 4: Subscriptions & Billing */}
      {activeTab === 'SUBSCRIPTIONS' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900">Recurring Billing Schedules</h3>
            <span className="text-xs text-purple-600 font-mono font-semibold">Proration Engine Active</span>
          </div>
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase font-semibold text-[10px]">
                <th className="py-3 px-4">Service</th>
                <th className="py-3 px-3">Interval</th>
                <th className="py-3 px-3">Units</th>
                <th className="py-3 px-3">Rate</th>
                <th className="py-3 px-3">Next Bill Date</th>
                <th className="py-3 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {subscriptions.map(s => (
                <tr key={s.id}>
                  <td className="py-3 px-4 font-bold text-slate-900">{s.productName}</td>
                  <td className="py-3 px-3 font-mono">{s.interval}</td>
                  <td className="py-3 px-3 font-mono font-semibold">{s.quantity}</td>
                  <td className="py-3 px-3 font-mono font-bold text-slate-900">${s.amount.toLocaleString()}</td>
                  <td className="py-3 px-3 font-mono text-slate-500">{s.nextBillingDate}</td>
                  <td className="py-3 px-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {s.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 5: Risk Scoring & Margin */}
      {activeTab === 'RISK' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
            </div>
          </div>

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
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
