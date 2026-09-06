import React, { useState, useEffect, useMemo } from 'react';
import { 
  Truck, 
  Warehouse as WarehouseIcon, 
  CheckCircle2, 
  AlertTriangle, 
  PackageCheck, 
  Boxes, 
  MapPin, 
  Edit3,
  Loader2
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/StatusBadge';
import { orderService, fulfillmentService } from '../../services/api';
import { 
  OrderResponse 
} from '../../services/orderService';
import { 
  FulfillmentResponse, 
  FulfillmentAllocationResponse,
  BackorderResponse
} from '../../services/fulfillmentService';

export const FulfillmentView: React.FC = () => {
  const { currentUser, showNotification } = useApp();
  const queryClient = useQueryClient();
  const role = (currentUser.role || '').toUpperCase();
  const isReadOnlyRep = role === 'SALES_REP' || role === 'CUSTOMER';
  const canAccept = ['ADMIN', 'FINANCE_OPERATIONS', 'SALES_MANAGER'].includes(role);
  const canOverride = ['ADMIN', 'FINANCE_OPERATIONS'].includes(role);

  const [activeOrderId, setActiveOrderId] = useState<string>('');
  const [isOverrideModalOpen, setIsOverrideModalOpen] = useState<boolean>(false);
  const [overrideMap, setOverrideMap] = useState<Record<string, number>>({});

  // 1. Fetch Orders to select from
  const { data: orders = [], isLoading: isOrdersLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: () => orderService.listOrders(),
  });

  // Set default activeOrderId when orders load
  useEffect(() => {
    if (!activeOrderId && orders.length > 0) {
      setActiveOrderId(orders[0].id);
    }
  }, [orders, activeOrderId]);

  // 2. Fetch Fulfillment details for selected order
  const { 
    data: fulfillment, 
    isLoading: isFulfillmentLoading 
  } = useQuery({
    queryKey: ['fulfillment', activeOrderId],
    queryFn: () => fulfillmentService.getFulfillment(activeOrderId),
    enabled: Boolean(activeOrderId),
  });

  // 3. Fetch Backorders
  const { data: backorders = [] } = useQuery({
    queryKey: ['backorders', activeOrderId],
    queryFn: () => fulfillmentService.listBackorders({ order_id: activeOrderId }),
    enabled: Boolean(activeOrderId),
  });

  const invalidateFulfillment = () => {
    queryClient.invalidateQueries({ queryKey: ['fulfillment', activeOrderId] });
    queryClient.invalidateQueries({ queryKey: ['backorders', activeOrderId] });
    queryClient.invalidateQueries({ queryKey: ['orders'] });
  };

  // Mutations
  const acceptMutation = useMutation({
    mutationFn: () => fulfillmentService.acceptFulfillment(activeOrderId),
    onSuccess: () => {
      invalidateFulfillment();
      showNotification('Warehouse allocation confirmed and marked for dispatch.', 'success');
    },
    onError: (err: any) => {
      showNotification(err?.response?.data?.detail || 'Failed to accept fulfillment.', 'error');
    },
  });

  const suggestMutation = useMutation({
    mutationFn: () => fulfillmentService.suggestFulfillment(activeOrderId),
    onSuccess: () => {
      invalidateFulfillment();
      showNotification('Suggested allocation recalculated against inventory levels.', 'info');
    },
    onError: (err: any) => {
      showNotification(err?.response?.data?.detail || 'Failed to calculate allocation.', 'error');
    },
  });

  const overrideMutation = useMutation({
    mutationFn: (allocations: Array<{ quotation_line_id: string; warehouse_id: string; quantity_allocated: number }>) =>
      fulfillmentService.overrideFulfillment(activeOrderId, { allocations }),
    onSuccess: () => {
      invalidateFulfillment();
      setIsOverrideModalOpen(false);
      showNotification('Fulfillment allocations manually committed.', 'success');
    },
    onError: (err: any) => {
      showNotification(err?.response?.data?.detail || 'Manual allocation override failed.', 'error');
    },
  });

  const allocations: FulfillmentAllocationResponse[] = fulfillment?.allocations || [];

  useEffect(() => {
    if (allocations.length > 0) {
      const initialMap: Record<string, number> = {};
      allocations.forEach((a, i) => {
        const key = a.id || `${a.warehouse_id}_${a.product_id}_${i}`;
        initialMap[key] = Number(a.quantity_allocated || 0);
      });
      setOverrideMap(initialMap);
    }
  }, [fulfillment, isOverrideModalOpen]);

  const handleAccept = () => {
    if (!activeOrderId) return;
    acceptMutation.mutate();
  };

  const handleSaveOverride = () => {
    if (!activeOrderId || allocations.length === 0) return;
    const payload = allocations.map((a, i) => {
      const key = a.id || `${a.warehouse_id}_${a.product_id}_${i}`;
      const qty = overrideMap[key] !== undefined ? overrideMap[key] : Number(a.quantity_allocated || 0);
      return {
        quotation_line_id: a.quotation_line_id || a.id,
        warehouse_id: a.warehouse_id,
        quantity_allocated: qty,
      };
    });
    overrideMutation.mutate(payload);
  };

  // Group allocations by warehouse
  const warehouseGroups = useMemo(() => {
    const groups: Record<string, { warehouseName: string; allocations: FulfillmentAllocationResponse[] }> = {};
    allocations.forEach(alloc => {
      const rawId = alloc.warehouse_id ? String(alloc.warehouse_id) : 'unassigned';
      if (!groups[rawId]) {
        groups[rawId] = {
          warehouseName: alloc.warehouse_name || (rawId !== 'unassigned' ? (rawId.length >= 8 ? `Warehouse ${rawId.substring(0, 8)}` : `Warehouse ${rawId}`) : 'Unassigned Hub'),
          allocations: [],
        };
      }
      groups[rawId].allocations.push(alloc);
    });
    return groups;
  }, [allocations]);

  const whKeys = Object.keys(warehouseGroups);
  const activeOrder = orders.find(o => o.id === activeOrderId);

  if (isOrdersLoading) {
    return (
      <div className="p-16 flex flex-col items-center justify-center text-slate-500 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="text-xs font-medium">Loading orders and fulfillment status...</span>
      </div>
    );
  }

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
                Tracking warehouse allocation and shipment splits for customer orders. Reallocation requires Finance/Ops privileges.
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
        {orders.length > 0 && (
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-slate-500">Order:</span>
            <select
              value={activeOrderId}
              onChange={(e) => setActiveOrderId(e.target.value)}
              className="text-xs bg-white border border-slate-200 rounded-lg px-3 py-1.5 font-bold text-blue-700 shadow-2xs focus:ring-1 focus:ring-blue-500"
            >
              {orders.map((o: OrderResponse) => (
                <option key={o.id} value={o.id}>
                  {o.order_number || o.id.substring(0, 8)} — {o.customer_name || 'Customer'}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {orders.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-xl border border-slate-200 text-slate-400 text-xs">
          No confirmed orders currently require fulfillment dispatch. Convert approved quotations to orders to initiate allocation.
        </div>
      ) : isFulfillmentLoading ? (
        <div className="p-12 flex justify-center items-center gap-2 text-slate-500 text-xs">
          <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
          <span>Loading allocation data...</span>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Order Banner & Status */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="w-11 h-11 rounded-lg bg-blue-50 border border-blue-200 text-blue-600 flex items-center justify-center font-bold">
                <Truck className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-slate-900">
                    {fulfillment?.order_number || activeOrder?.order_number || activeOrderId.substring(0, 8)}
                  </h3>
                  <StatusBadge status={fulfillment?.order_status || fulfillment?.status || activeOrder?.status || 'PENDING'} />
                </div>
                <div className="text-xs text-slate-500 mt-0.5">
                  Customer: <strong className="text-slate-800">{fulfillment?.customer_name || activeOrder?.customer_name || 'Customer Account'}</strong>
                </div>
              </div>
            </div>

            {/* Split Metrics */}
            <div className="flex items-center gap-4 text-xs">
              <div className="px-3.5 py-2 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block">Shipment Hubs</span>
                <span className="font-mono font-bold text-slate-900 text-sm">{fulfillment?.estimated_shipment_count ?? (whKeys.length || 1)} Location(s)</span>
              </div>
              <div className="px-3.5 py-2 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block">Allocated Lines</span>
                <span className="font-mono font-bold text-slate-900 text-sm">{allocations.length} Units/Lines</span>
              </div>
            </div>
          </div>

          {/* Backorder Banner if present */}
          {backorders.length > 0 && (
            <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-amber-500 text-white flex items-center justify-center shrink-0 shadow-xs">
                  <Boxes className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-amber-950">Active Backorder Pending ({backorders.length} Item(s))</h4>
                  <p className="text-[11px] text-amber-800 mt-0.5">
                    Insufficient warehouse stock triggered automated backorder routing. Stock will be dispatched upon replenishment.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Dynamic Warehouse Allocation Cards */}
          {whKeys.length === 0 ? (
            <div className="p-8 text-center bg-white rounded-xl border border-slate-200 text-slate-400 text-xs">
              <p>No active warehouse allocations for this order.</p>
              {!isReadOnlyRep && (
                <button
                  onClick={() => suggestMutation.mutate()}
                  disabled={suggestMutation.isPending}
                  className="mt-3 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded-lg font-medium"
                >
                  Generate Suggested Allocation
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {whKeys.map((whId, idx) => {
                const group = warehouseGroups[whId];
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
                            <MapPin className="w-3 h-3" /> Facility ID: {whId}
                          </span>
                        </div>
                      </div>
                      <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                        Shipment Hub {idx + 1}
                      </span>
                    </div>

                    {/* Items allocated from this warehouse */}
                    <div className="space-y-2">
                      {group.allocations.map((item, itemIdx) => (
                        <div key={item.id || itemIdx} className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                          <div>
                            <div className="font-semibold text-slate-900">{item.product_name || 'Product'}</div>
                            <div className="text-[10px] text-slate-400 font-mono">ID: {item.product_id || item.id}</div>
                          </div>
                          <div className="text-right">
                            <span className="font-bold font-mono text-sm text-blue-700">{Number(item.quantity_allocated || 0)} Units</span>
                            <span className="block text-[10px] text-slate-400">Allocated</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Allocation Actions Bar */}
          {!isReadOnlyRep && (
            <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-wrap items-center justify-between gap-4">
              <div className="text-xs text-slate-500">
                <span className="font-semibold text-slate-800">Warehouse Routing:</span> Multi-location fulfillment balances inventory distribution and shipping logistics.
              </div>

              <div className="flex items-center gap-2.5">
                {canOverride && (
                  <button
                    onClick={() => setIsOverrideModalOpen(true)}
                    disabled={allocations.length === 0}
                    className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition cursor-pointer disabled:opacity-50"
                  >
                    <Edit3 className="w-3.5 h-3.5 text-slate-500" />
                    <span>Manual Override</span>
                  </button>
                )}

                {canAccept && (
                  <button
                    onClick={handleAccept}
                    disabled={acceptMutation.isPending || fulfillment?.order_status === 'ACCEPTED' || fulfillment?.order_status === 'FULFILLED' || fulfillment?.status === 'ACCEPTED' || fulfillment?.status === 'FULFILLED'}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>{(fulfillment?.order_status === 'ACCEPTED' || fulfillment?.status === 'ACCEPTED' || fulfillment?.order_status === 'FULFILLED') ? 'Allocation Confirmed' : 'Confirm & Dispatch Split'}</span>
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Manual Override Modal */}
          {isOverrideModalOpen && (
            <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
              <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-lg w-full p-5 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h3 className="text-sm font-bold text-slate-900">Manual Allocation Override</h3>
                  <button
                    onClick={() => setIsOverrideModalOpen(false)}
                    className="text-slate-400 hover:text-slate-600"
                  >
                    ✕
                  </button>
                </div>

                <div className="space-y-3 text-xs">
                  <p className="text-slate-600">
                    Adjust units allocated from each warehouse for order <strong className="text-slate-900 font-mono">{activeOrderId}</strong>:
                  </p>

                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {allocations.map((alloc, idx) => {
                      const key = alloc.id || `${alloc.warehouse_id}_${alloc.product_id}_${idx}`;
                      const currentVal = overrideMap[key] !== undefined ? overrideMap[key] : Number(alloc.quantity_allocated || 0);
                      return (
                        <div key={key} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
                          <div>
                            <div className="font-semibold text-slate-800">{alloc.product_name || 'Product'}</div>
                            <div className="text-[10px] text-slate-500">{alloc.warehouse_name || alloc.warehouse_id}</div>
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
                    disabled={overrideMutation.isPending}
                    className="px-4 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-2xs disabled:opacity-50"
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
