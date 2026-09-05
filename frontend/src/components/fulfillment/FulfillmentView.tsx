import React, { useState } from 'react';
import { 
  Truck, 
  Warehouse as WarehouseIcon, 
  Layers, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw, 
  PackageCheck, 
  Split, 
  ArrowRight,
  Boxes,
  MapPin,
  Sparkles,
  Edit3
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/StatusBadge';

export const FulfillmentView: React.FC = () => {
  const { 
    fulfillments, 
    acceptSuggestedSplit, 
    overrideAllocation, 
    consolidateBackorder, 
    showNotification 
  } = useApp();

  const [activeOrderId, setActiveOrderId] = useState<string>('ord-1051');
  const [isOverrideModalOpen, setIsOverrideModalOpen] = useState<boolean>(false);
  const [overrideWh1, setOverrideWh1] = useState<number>(7);
  const [overrideWh2, setOverrideWh2] = useState<number>(3);

  const activeFulfillment = fulfillments[activeOrderId] || Object.values(fulfillments)[0];

  const handleAccept = () => {
    if (!activeFulfillment) return;
    acceptSuggestedSplit(activeFulfillment.orderId);
  };

  const handleConsolidate = () => {
    if (!activeFulfillment) return;
    consolidateBackorder(activeFulfillment.orderId);
  };

  const handleSaveOverride = () => {
    if (!activeFulfillment) return;
    const updated = activeFulfillment.allocations.map(a => {
      if (a.warehouseId === 'wh-1' && a.productId === 'prod-1') {
        return { ...a, quantityAllocated: overrideWh1 };
      }
      if (a.warehouseId === 'wh-2' && a.productId === 'prod-1') {
        return { ...a, quantityAllocated: overrideWh2 };
      }
      return a;
    });
    overrideAllocation(activeFulfillment.orderId, updated);
    setIsOverrideModalOpen(false);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Multi-Warehouse Fulfillment & Allocation</h2>
          <p className="text-xs text-slate-500 mt-0.5">Automated stock routing, warehouse split optimization, shipment minimization, and backorder handling.</p>
        </div>

        {/* Order Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-slate-500">Order:</span>
          <select
            value={activeOrderId}
            onChange={(e) => setActiveOrderId(e.target.value)}
            className="text-xs bg-white border border-slate-200 rounded-lg px-3 py-1.5 font-bold text-blue-700 shadow-2xs focus:ring-1 focus:ring-blue-500"
          >
            <option value="ord-1051">ORD-1051 — Orion Manufacturing (10 Servers, 4 Modules)</option>
          </select>
        </div>
      </div>

      {activeFulfillment && (
        <div className="space-y-6">
          {/* Order Banner & Status */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="w-11 h-11 rounded-lg bg-blue-50 border border-blue-200 text-blue-600 flex items-center justify-center font-bold">
                <Truck className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-slate-900">{activeFulfillment.orderId.toUpperCase()}</h3>
                  <StatusBadge status={activeFulfillment.status} />
                </div>
                <div className="text-xs text-slate-500 mt-0.5">
                  Customer: <strong className="text-slate-800">{activeFulfillment.customerName}</strong> • Linked Quote: {activeFulfillment.quoteNumber}
                </div>
              </div>
            </div>

            {/* Split Metrics */}
            <div className="flex items-center gap-4 text-xs">
              <div className="px-3.5 py-2 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block">Shipment Count</span>
                <span className="font-mono font-bold text-slate-900 text-sm">{activeFulfillment.totalShipments} Separate Shipments</span>
              </div>
              <div className="px-3.5 py-2 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block">Estimated Freight Cost</span>
                <span className="font-mono font-bold text-slate-900 text-sm">${activeFulfillment.totalShippingCost}</span>
              </div>
            </div>
          </div>

          {/* Backorder Consolidation Prompt (Problem statement B6 / FR-13.2) */}
          {activeFulfillment.consolidationAvailable && activeFulfillment.backorderQuantity > 0 && (
            <div className="p-4 rounded-xl bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-300 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-amber-500 text-white flex items-center justify-center shrink-0 shadow-xs">
                  <Boxes className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-amber-950 flex items-center gap-1.5">
                    <span>Stock replenishment arrived at East Coast Depot!</span>
                    <span className="px-1.5 py-0.2 rounded bg-amber-200 text-amber-900 text-[10px] font-mono">Consolidation Available</span>
                  </div>
                  <p className="text-xs text-amber-900/80 mt-0.5">
                    1 unit of AI Inference Acceleration Module can now be consolidated from Newark, eliminating a separate delayed shipment.
                  </p>
                </div>
              </div>

              <button
                onClick={handleConsolidate}
                className="shrink-0 px-3.5 py-2 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold shadow-xs transition flex items-center gap-1.5 cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Consolidate Remaining Backorder</span>
              </button>
            </div>
          )}

          {/* Recommended Warehouse Split Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Warehouse 1: Main Distribution Center (Chicago) */}
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center">
                    <WarehouseIcon className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">Main Distribution Center</h4>
                    <span className="text-[11px] text-slate-400 flex items-center gap-1">
                      <MapPin className="w-3 h-3" /> Chicago, IL (ORD-MAIN) • Weight: 1.0x
                    </span>
                  </div>
                </div>
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                  Shipment 1 of 2
                </span>
              </div>

              {/* Items allocated from WH-1 */}
              <div className="space-y-2">
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-slate-900">Enterprise Edge Server X4</div>
                    <div className="text-[10px] text-slate-400 font-mono">SKU: HW-SRV-X4</div>
                  </div>
                  <div className="text-right">
                    <span className="font-bold font-mono text-sm text-blue-700">6 Units</span>
                    <span className="block text-[10px] text-slate-400">of 6 in stock (100%)</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-slate-900">AI Inference Acceleration Module</div>
                    <div className="text-[10px] text-slate-400 font-mono">SKU: HW-AI-ACC</div>
                  </div>
                  <div className="text-right">
                    <span className="font-bold font-mono text-sm text-blue-700">2 Units</span>
                    <span className="block text-[10px] text-slate-400">of 2 in stock (100%)</span>
                  </div>
                </div>
              </div>

              <div className="text-xs text-slate-500 pt-2 border-t border-slate-100 flex justify-between">
                <span>Estimated dispatch transit: <strong>2 Business Days</strong></span>
                <span className="font-mono font-semibold text-slate-700">Freight: $520</span>
              </div>
            </div>

            {/* Warehouse 2: East Coast Depot (Newark) */}
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center">
                    <WarehouseIcon className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">East Coast Depot</h4>
                    <span className="text-[11px] text-slate-400 flex items-center gap-1">
                      <MapPin className="w-3 h-3" /> Newark, NJ (EWR-DEPOT) • Weight: 1.3x
                    </span>
                  </div>
                </div>
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                  Shipment 2 of 2
                </span>
              </div>

              {/* Items allocated from WH-2 */}
              <div className="space-y-2">
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-slate-900">Enterprise Edge Server X4</div>
                    <div className="text-[10px] text-slate-400 font-mono">SKU: HW-SRV-X4 (Split balance)</div>
                  </div>
                  <div className="text-right">
                    <span className="font-bold font-mono text-sm text-blue-700">4 Units</span>
                    <span className="block text-[10px] text-slate-400">of 4 in stock (100%)</span>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-slate-900">AI Inference Acceleration Module</div>
                    <div className="text-[10px] text-slate-400 font-mono">SKU: HW-AI-ACC</div>
                  </div>
                  <div className="text-right">
                    <span className="font-bold font-mono text-sm text-blue-700">1 Unit</span>
                    <span className="block text-[10px] text-slate-400">of 1 in stock</span>
                  </div>
                </div>
              </div>

              {/* Backorder notice */}
              {activeFulfillment.backorderQuantity > 0 && (
                <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                    <span>1 Unit of AI Acceleration Module on Backorder</span>
                  </div>
                  <span className="font-mono font-bold">ETA: 3 Days</span>
                </div>
              )}

              <div className="text-xs text-slate-500 pt-2 border-t border-slate-100 flex justify-between">
                <span>Estimated dispatch transit: <strong>3 Business Days</strong></span>
                <span className="font-mono font-semibold text-slate-700">Freight: $400</span>
              </div>
            </div>
          </div>

          {/* Allocation Actions Bar */}
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
            <div className="text-xs text-slate-500">
              <span className="font-semibold text-slate-800">Warehouse Optimization:</span> Stock allocation minimized shipments to 2 hubs while prioritizing lowest freight cost weightings.
            </div>

            <div className="flex items-center gap-2.5">
              <button
                onClick={() => setIsOverrideModalOpen(true)}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition cursor-pointer"
              >
                <Edit3 className="w-3.5 h-3.5 text-slate-500" />
                <span>Manual Override</span>
              </button>

              <button
                onClick={handleAccept}
                disabled={activeFulfillment.status === 'ACCEPTED' || activeFulfillment.status === 'FULFILLED'}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{activeFulfillment.status === 'ACCEPTED' ? 'Split Accepted' : 'Accept Suggested Split'}</span>
              </button>
            </div>
          </div>

          {/* Manual Override Modal */}
          {isOverrideModalOpen && (
            <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
              <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-lg w-full p-5 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h3 className="text-sm font-bold text-slate-900">Manual Allocation Override — Enterprise Edge Server</h3>
                  <button
                    onClick={() => setIsOverrideModalOpen(false)}
                    className="text-slate-400 hover:text-slate-600"
                  >
                    ×
                  </button>
                </div>

                <div className="space-y-3 text-xs">
                  <p className="text-slate-600">
                    Total Required: <strong className="text-slate-900 font-mono">10 Units</strong>. Reallocate stock pull between hubs:
                  </p>

                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
                    <label className="flex items-center justify-between">
                      <span className="font-semibold text-slate-800">Main Distribution Center (Chicago):</span>
                      <input
                        type="number"
                        min="0"
                        max="10"
                        value={overrideWh1}
                        onChange={(e) => setOverrideWh1(parseInt(e.target.value) || 0)}
                        className="w-16 px-2 py-1 text-right font-mono font-bold bg-white border border-slate-300 rounded"
                      />
                    </label>
                    <label className="flex items-center justify-between">
                      <span className="font-semibold text-slate-800">East Coast Depot (Newark):</span>
                      <input
                        type="number"
                        min="0"
                        max="10"
                        value={overrideWh2}
                        onChange={(e) => setOverrideWh2(parseInt(e.target.value) || 0)}
                        className="w-16 px-2 py-1 text-right font-mono font-bold bg-white border border-slate-300 rounded"
                      />
                    </label>
                  </div>

                  <div className="text-[11px] text-slate-500">
                    Sum: <strong className={overrideWh1 + overrideWh2 === 10 ? 'text-emerald-600' : 'text-rose-600'}>{overrideWh1 + overrideWh2}</strong> / 10 required
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                  <button
                    onClick={() => setIsOverrideModalOpen(false)}
                    className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveOverride}
                    disabled={overrideWh1 + overrideWh2 !== 10}
                    className="px-4 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg shadow-2xs"
                  >
                    Commit Override
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
