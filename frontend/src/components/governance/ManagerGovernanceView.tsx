import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Sliders, 
  Percent, 
  Save
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { AccessRestrictedView } from '../common/AccessRestrictedView';

const DEFAULT_GOVERNANCE = {
  managerCeiling: 15,
  tierPlatinum: 25,
  tierGold: 18,
  tierSilver: 12,
  tierBronze: 8,
  catHardware: 15,
  catSubscription: 25,
  catServices: 20,
  riskThresholdManager: 40,
  minMarginFloor: 25,
};

export const ManagerGovernanceView: React.FC = () => {
  const { showNotification, currentUser } = useApp();

  // Defense-in-depth RBAC check
  if (currentUser.role !== 'SALES_MANAGER' && currentUser.role !== 'ADMIN') {
    return (
      <AccessRestrictedView
        requiredRole="Sales Manager or Administrator"
        featureName="Sales Manager Commercial Governance"
      />
    );
  }

  // Manager-accessible governance controls
  const [managerCeiling, setManagerCeiling] = useState(() => {
    const saved = localStorage.getItem('dealflow_gov_mgr_ceiling');
    return saved ? parseInt(saved) : DEFAULT_GOVERNANCE.managerCeiling;
  });
  const [tierPlatinum, setTierPlatinum] = useState(() => {
    const saved = localStorage.getItem('dealflow_gov_tier_plat');
    return saved ? parseInt(saved) : DEFAULT_GOVERNANCE.tierPlatinum;
  });
  const [tierGold, setTierGold] = useState(() => {
    const saved = localStorage.getItem('dealflow_gov_tier_gold');
    return saved ? parseInt(saved) : DEFAULT_GOVERNANCE.tierGold;
  });
  const [tierSilver, setTierSilver] = useState(() => {
    const saved = localStorage.getItem('dealflow_gov_tier_silver');
    return saved ? parseInt(saved) : DEFAULT_GOVERNANCE.tierSilver;
  });
  const [tierBronze, setTierBronze] = useState(() => {
    const saved = localStorage.getItem('dealflow_gov_tier_bronze');
    return saved ? parseInt(saved) : DEFAULT_GOVERNANCE.tierBronze;
  });

  const [catHardware, setCatHardware] = useState(DEFAULT_GOVERNANCE.catHardware);
  const [catSubscription, setCatSubscription] = useState(DEFAULT_GOVERNANCE.catSubscription);
  const [catServices, setCatServices] = useState(DEFAULT_GOVERNANCE.catServices);

  const [riskThresholdManager, setRiskThresholdManager] = useState(DEFAULT_GOVERNANCE.riskThresholdManager);
  const [minMarginFloor, setMinMarginFloor] = useState(DEFAULT_GOVERNANCE.minMarginFloor);

  const handleSavePolicy = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('dealflow_gov_mgr_ceiling', String(managerCeiling));
    localStorage.setItem('dealflow_gov_tier_plat', String(tierPlatinum));
    localStorage.setItem('dealflow_gov_tier_gold', String(tierGold));
    localStorage.setItem('dealflow_gov_tier_silver', String(tierSilver));
    localStorage.setItem('dealflow_gov_tier_bronze', String(tierBronze));
    showNotification('Manager commercial governance parameters updated.', 'success');
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Sales Operations Governance & Thresholds</h2>
          <p className="text-xs text-slate-500 mt-0.5">Manager-level controls for tier discount ceilings, category caps, margin protection floor, and approval triggers.</p>
        </div>

        <button
          onClick={handleSavePolicy}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
        >
          <Save className="w-3.5 h-3.5" />
          <span>Save Manager Governance</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tier Ceilings */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <Percent className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-bold text-slate-900">Customer Tier Discount Ceilings</h3>
          </div>

          <div className="space-y-3.5 text-xs">
            <div>
              <div className="flex justify-between font-semibold text-slate-700 mb-1">
                <span>Platinum Tier Max:</span>
                <span className="font-mono font-bold text-blue-600">{tierPlatinum}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="35"
                value={tierPlatinum}
                onChange={(e) => setTierPlatinum(parseInt(e.target.value))}
                className="w-full accent-blue-600"
              />
            </div>

            <div>
              <div className="flex justify-between font-semibold text-slate-700 mb-1">
                <span>Gold Tier Max:</span>
                <span className="font-mono font-bold text-blue-600">{tierGold}%</span>
              </div>
              <input
                type="range"
                min="5"
                max="25"
                value={tierGold}
                onChange={(e) => setTierGold(parseInt(e.target.value))}
                className="w-full accent-blue-600"
              />
            </div>

            <div>
              <div className="flex justify-between font-semibold text-slate-700 mb-1">
                <span>Silver Tier Max:</span>
                <span className="font-mono font-bold text-blue-600">{tierSilver}%</span>
              </div>
              <input
                type="range"
                min="5"
                max="20"
                value={tierSilver}
                onChange={(e) => setTierSilver(parseInt(e.target.value))}
                className="w-full accent-blue-600"
              />
            </div>

            <div>
              <div className="flex justify-between font-semibold text-slate-700 mb-1">
                <span>Bronze Tier Max:</span>
                <span className="font-mono font-bold text-blue-600">{tierBronze}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="15"
                value={tierBronze}
                onChange={(e) => setTierBronze(parseInt(e.target.value))}
                className="w-full accent-blue-600"
              />
            </div>
          </div>
        </div>

        {/* Product Category Ceilings */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <Sliders className="w-4 h-4 text-emerald-600" />
            <h3 className="text-sm font-bold text-slate-900">Category Ceilings</h3>
          </div>

          <div className="space-y-3.5 text-xs">
            <div>
              <div className="flex justify-between font-semibold text-slate-700 mb-1">
                <span>Hardware Components:</span>
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
                <span>Subscriptions:</span>
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
                <span>Services:</span>
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
          </div>
        </div>

        {/* Risk Threshold & Margin Floor */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <ShieldCheck className="w-4 h-4 text-purple-600" />
            <h3 className="text-sm font-bold text-slate-900">Approval Routing & Floors</h3>
          </div>

          <div className="space-y-3.5 text-xs">
            <div>
              <div className="flex justify-between font-semibold text-slate-700 mb-1">
                <span>Manager Discretion Ceiling:</span>
                <span className="font-mono font-bold text-purple-600">{managerCeiling}%</span>
              </div>
              <input
                type="range"
                min="10"
                max="25"
                value={managerCeiling}
                onChange={(e) => setManagerCeiling(parseInt(e.target.value))}
                className="w-full accent-purple-600"
              />
            </div>

            <div>
              <div className="flex justify-between font-semibold text-slate-700 mb-1">
                <span>Manager Approval Risk Trigger:</span>
                <span className="font-mono font-bold text-purple-600">{riskThresholdManager} pts</span>
              </div>
              <input
                type="range"
                min="30"
                max="60"
                value={riskThresholdManager}
                onChange={(e) => setRiskThresholdManager(parseInt(e.target.value))}
                className="w-full accent-purple-600"
              />
              <span className="text-[11px] text-slate-400">Quotes scoring ≥ {riskThresholdManager} risk require Level 1 review.</span>
            </div>

            <div>
              <div className="flex justify-between font-semibold text-slate-700 mb-1">
                <span>Gross Margin Protection Floor:</span>
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
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
