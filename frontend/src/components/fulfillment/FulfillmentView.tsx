import React, { useState, useEffect } from 'react';
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
import { OrderFulfillment } from '../../types';

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

  const activeFulfillment = fulfillments[activeOrderId] || Object.values(fulfillments)[0];

  // Dynamic editable allocation map initialized from active order allocations
  const [overrideMap, setOverrideMap] = useState<Record<string, number>>({});

  useEffect(() => {
    if (activeFulfillment) {
      const initialMap: Record<string, number> = {};
      activeFulfillment.allocations.forEach((a, i) => {
        initialMap[`${a.warehouseId}_${a.productId}_${i}`] = a.quantityAllocated;
      });
      setOverrideMap(initialMap);
    }
  }, [activeFulfillment, isOverrideModalOpen]);

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
    const updated = activeFulfillment.allocations.map((a, i) => {
      const key = `${a.warehouseId}_${a.productId}_${i}`;
      const qty = overrideMap[key] !== undefined ? overrideMap[key] : a.quantityAllocated;
      return { ...a, quantityAllocated: qty };
    });
    overrideAllocation(activeFulfillment.orderId, updated);
    setIsOverrideModalOpen(false);
  };

  const { currentUser } = useApp();
  const isReadOnlyRep = currentUser.role === 'SALES_REP';

  // Group allocations by warehouse dynamically
  const warehouseGroups = React.useMemo(() => {
    if (!activeFulfillment) return {};
    const groups: Record<string, { warehouseName: string; allocations: typeof activeFulfillment.allocations; totalFreight: number }> = {};
    activeFulfillment.allocations.forEach(alloc => {
      if (!groups[alloc.warehouseId]) {
        groups[alloc.warehouseId] = {
          warehouseName: alloc.warehouseName,
          allocations: [],
          totalFreight: 0
        };
      }
      groups[alloc.warehouseId].allocations.push(alloc);
      groups[alloc.warehouseId].totalFreight += alloc.estimatedCost || 0;
    });
    return groups;
  }, [activeFulfillment]);

  const whKeys = Object.keys(warehouseGroups);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Read-Only Notice for Sales Rep */}
      {isReadOnlyRep && (
        <div className="p-4 rounded-xl bg-blue-50/80 border border-blue-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <PackageCheck className="w-5 h-5 text-blue-600 shrink-0" />
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-blue-900">Sales Representative View &bull; Order Tracking Mode</span>
                <span className="text-[10px] bg-blue-100 text-blue-700 font-bold px-2 py-0.5 rounded-full">View Only</span>
              </div>
              <p className="text-[11px] text-blue-700 mt-0.5">
                Tracking warehouse allocation and shipment splits for your customer deals. Physical inventory reallocation requires Fulfillment Operations role.
              </p>
            </div>
          </div>
        </div>
      )}

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
            {(Object.values(fulfillments) as OrderFulfillment[]).map(f => (
              <option key={f.orderId} value={f.orderId}>
                {f.orderId.toUpperCase()} — {f.customerName} ({f.totalShipments} Shipments)
              </option>
            ))}
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

          {/* Backorder Consolidation Prompt */}
          {activeFulfillment.consolidationAvailable && activeFulfillment.backorderQuantity > 0 && (
            <div className="p-4 rounded-xl bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-300 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-amber-500 text-white flex items-center justify-center shrink-0 shadow-xs">
                  <Boxes className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-amber-950">Shipment Minimization Available (Hold for Single Dispatch)</h4>
                  <p className="text-[11px] text-amber-800 mt-0.5">
                    {activeFulfillment.backorderProductNames[0] || '1 Item on backorder'}. Consolidating into 1 shipment reduces freight from ${activeFulfillment.totalShippingCost} to $640 (saves $280).
                  </p>
                </div>
              </div>

              {!isReadOnlyRep && (
                <button
                  onClick={handleConsolidate}
                  className="px-3.5 py-2 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs shadow-xs transition shrink-0 cursor-pointer"
                >
                  Hold & Consolidate (1 Shipment)
                </button>
              )}
            </div>
          )}

          {/* Dynamic Warehouse Allocation Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {whKeys.map((whId, idx) => {
              const group = warehouseGroups[whId];
              const isWh1 = whId === 'wh-1';

              return (
                <div key={whId} className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                        <WarehouseIcon className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-slate-900">{group.warehouseName}</h4>
                        <span className="text-[11px] text-slate-400 flex items-center gap-1">
                          <MapPin className="w-3 h-3" /> {isWh1 ? 'Chicago, IL (ORD-MAIN) • Weight: 1.0x' : 'Newark, NJ (EWR-DEPOT) • Weight: 1.3x'}
                        </span>
                      </div>
                    </div>
                    <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                      Shipment {idx + 1} of {whKeys.length}
                    </span>
                  </div>

                  {/* Items allocated from this warehouse */}
                  <div className="space-y-2">
                    {group.allocations.map((item, itemIdx) => (
                      <div key={itemIdx} className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                        <div>
                          <div className="font-semibold text-slate-900">{item.productName}</div>
                          <div className="text-[10px] text-slate-400 font-mono">SKU: {item.productId.toUpperCase()}</div>
                        </div>
                        <div className="text-right">
                          <span className="font-bold font-mono text-sm text-blue-700">{item.quantityAllocated} Units</span>
                          <span className="block text-[10px] text-slate-400">Allocated</span>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Backorder notice on second warehouse */}
                  {!isWh1 && activeFulfillment.backorderQuantity > 0 && (
                    <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                        <span>{activeFulfillment.backorderQuantity} Unit on Backorder</span>
                      </div>
                      <span className="font-mono font-bold">ETA: 3 Days</span>
                    </div>
                  )}

                  <div className="text-xs text-slate-500 pt-2 border-t border-slate-100 flex justify-between">
                    <span>Estimated dispatch transit: <strong>{isWh1 ? '2 Business Days' : '3 Business Days'}</strong></span>
                    <span className="font-mono font-semibold text-slate-700">Freight: ${group.totalFreight || (isWh1 ? 520 : 400)}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Allocation Actions Bar (Only if fulfillment operations / admin) */}
          {!isReadOnlyRep && (
            <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
              <div className="text-xs text-slate-500">
                <span className="font-semibold text-slate-800">Warehouse Optimization:</span> Stock allocation minimized shipments to {whKeys.length} hubs while prioritizing lowest freight cost weightings.
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
          )}

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
                    Adjust units allocated from each warehouse hub for order <strong className="text-slate-900 font-mono">{activeFulfillment.orderId.toUpperCase()}</strong>:
                  </p>

                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {activeFulfillment.allocations.map((alloc, idx) => {
                      const key = `${alloc.warehouseId}_${alloc.productId}_${idx}`;
                      const currentVal = overrideMap[key] !== undefined ? overrideMap[key] : alloc.quantityAllocated;
                      return (
                        <div key={key} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
                          <div>
                            <div className="font-semibold text-slate-800">{alloc.productName}</div>
                            <div className="text-[10px] text-slate-500">{alloc.warehouseName}</div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] text-slate-400">Qty:</span>
                            <input
                              type="number"
                              min="0"
                              value={currentVal}
                              onChange={(e) => {
                                const val = parseInt(e.target.value) || 0;
                                setOverrideMap(prev => ({ ...prev, [key]: val }));
                              }}
                              className="w-16 px-2 py-1 text-right font-mono font-bold bg-white border border-slate-300 rounded"
                            />
                          </div>
                        </div>
                      );
                    })}
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
                    className="px-4 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-2xs"
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
