import React, { useState, useMemo } from 'react';
import { 
  Plus, 
  Trash2, 
  Sparkles, 
  ShieldAlert, 
  CheckCircle2, 
  ArrowRight, 
  TrendingUp, 
  AlertTriangle, 
  Building2, 
  RotateCcw, 
  Send, 
  Check, 
  ShoppingBag, 
  Lock, 
  History, 
  ChevronDown, 
  ChevronUp,
  Loader2
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/StatusBadge';
import { RiskBadge } from '../common/RiskBadge';
import { 
  quotationService, 
  catalogService, 
  customerService, 
  approvalService 
} from '../../services/api';
import { QuotationLineResponse } from '../../services/quotationService';

export const QuoteBuilder: React.FC = () => {
  const { 
    selectedQuoteId, 
    setCurrentPage, 
    currentUser, 
    showNotification 
  } = useApp();

  const queryClient = useQueryClient();
  const [selectedAddProductId, setSelectedAddProductId] = useState<string>('');
  const [showAuditTrail, setShowAuditTrail] = useState<boolean>(false);

  // 1. Fetch Quotation
  const { 
    data: quotation, 
    isLoading: isQuoteLoading, 
    error: quoteError 
  } = useQuery({
    queryKey: ['quotation', selectedQuoteId],
    queryFn: () => quotationService.getQuotation(selectedQuoteId),
    enabled: Boolean(selectedQuoteId),
  });

  // 2. Fetch Lines
  const { 
    data: lines = [], 
    isLoading: isLinesLoading 
  } = useQuery({
    queryKey: ['quotation-lines', selectedQuoteId],
    queryFn: () => quotationService.getLines(selectedQuoteId),
    enabled: Boolean(selectedQuoteId),
  });

  // 3. Fetch Products for adding
  const { data: products = [] } = useQuery({
    queryKey: ['products'],
    queryFn: () => catalogService.getProducts(),
  });

  // 4. Fetch Customers
  const { data: customers = [] } = useQuery({
    queryKey: ['customers'],
    queryFn: () => customerService.getCustomers(),
  });

  // 5. Fetch Risk Assessment
  const { data: riskData } = useQuery({
    queryKey: ['quotation-risk', selectedQuoteId],
    queryFn: () => quotationService.getRisk(selectedQuoteId),
    enabled: Boolean(selectedQuoteId),
  });

  // 6. Fetch Approvals for this quote
  const { data: approvals = [] } = useQuery({
    queryKey: ['quotation-approvals', selectedQuoteId],
    queryFn: () => quotationService.getApprovals(selectedQuoteId),
    enabled: Boolean(selectedQuoteId),
  });

  // 7. Fetch Audit Logs
  const { data: auditLogs = [] } = useQuery({
    queryKey: ['quotation-audit-log', selectedQuoteId],
    queryFn: () => quotationService.getAuditLog(selectedQuoteId),
    enabled: Boolean(selectedQuoteId && showAuditTrail),
  });

  const invalidateQuote = () => {
    queryClient.invalidateQueries({ queryKey: ['quotation', selectedQuoteId] });
    queryClient.invalidateQueries({ queryKey: ['quotation-lines', selectedQuoteId] });
    queryClient.invalidateQueries({ queryKey: ['quotation-risk', selectedQuoteId] });
    queryClient.invalidateQueries({ queryKey: ['quotation-approvals', selectedQuoteId] });
    queryClient.invalidateQueries({ queryKey: ['quotations'] });
    queryClient.invalidateQueries({ queryKey: ['pipeline'] });
  };

  // Line Mutations
  const addLineMutation = useMutation({
    mutationFn: (productId: string) => quotationService.addLine(selectedQuoteId, { product_id: productId, quantity: 1 }),
    onSuccess: () => {
      invalidateQuote();
      setSelectedAddProductId('');
      showNotification('Product line added to quotation', 'success');
    },
    onError: (err: any) => {
      showNotification(err?.response?.data?.detail || 'Failed to add product line', 'error');
    },
  });

  const updateLineMutation = useMutation({
    mutationFn: ({ lineId, payload }: { lineId: string; payload: any }) =>
      quotationService.updateLine(selectedQuoteId, lineId, payload),
    onSuccess: () => {
      invalidateQuote();
    },
    onError: (err: any) => {
      showNotification(err?.response?.data?.detail || 'Failed to update line', 'error');
    },
  });

  const deleteLineMutation = useMutation({
    mutationFn: (lineId: string) => quotationService.deleteLine(selectedQuoteId, lineId),
    onSuccess: () => {
      invalidateQuote();
      showNotification('Line removed from quotation', 'info');
    },
    onError: (err: any) => {
      showNotification(err?.response?.data?.detail || 'Failed to remove line', 'error');
    },
  });

  // Action Mutations
  const recalculateMutation = useMutation({
    mutationFn: () => quotationService.recalculate(selectedQuoteId),
    onSuccess: () => {
      invalidateQuote();
      showNotification('Quotation recalculated against active discount policies', 'success');
    },
  });

  const submitMutation = useMutation({
    mutationFn: () => quotationService.submit(selectedQuoteId),
    onSuccess: () => {
      invalidateQuote();
      showNotification('Quotation submitted for governance review', 'success');
    },
    onError: (err: any) => {
      showNotification(err?.response?.data?.detail || 'Submission rejected by policy engine', 'error');
    },
  });

  const sendMutation = useMutation({
    mutationFn: () => quotationService.send(selectedQuoteId),
    onSuccess: () => {
      invalidateQuote();
      showNotification('Quotation sent to customer portal', 'success');
    },
    onError: (err: any) => {
      showNotification(err?.response?.data?.detail || 'Failed to send quote', 'error');
    },
  });

  const confirmMutation = useMutation({
    mutationFn: () => quotationService.confirm(selectedQuoteId),
    onSuccess: () => {
      invalidateQuote();
      showNotification('Quotation confirmed as official order!', 'success');
    },
    onError: (err: any) => {
      showNotification(err?.response?.data?.detail || 'Confirmation failed', 'error');
    },
  });

  if (!selectedQuoteId) {
    return (
      <div className="p-12 text-center text-slate-500">
        <Building2 className="w-10 h-10 mx-auto text-slate-400 mb-3" />
        <h3 className="text-base font-bold text-slate-700">No Quotation Selected</h3>
        <p className="text-xs text-slate-400 mt-1">Select an active deal from the quotations list to inspect or modify.</p>
        <button
          onClick={() => setCurrentPage('quotations')}
          className="mt-4 px-4 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700"
        >
          View All Quotations
        </button>
      </div>
    );
  }

  if (isQuoteLoading) {
    return (
      <div className="p-16 flex flex-col items-center justify-center text-slate-500 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="text-xs font-medium">Loading quotation details...</span>
      </div>
    );
  }

  if (quoteError || !quotation) {
    return (
      <div className="p-12 text-center text-rose-600">
        <AlertTriangle className="w-10 h-10 mx-auto mb-3" />
        <h3 className="text-base font-bold">Failed to load quotation</h3>
        <p className="text-xs text-slate-500 mt-1">The requested quotation could not be retrieved from the server.</p>
        <button
          onClick={() => setCurrentPage('quotations')}
          className="mt-4 px-4 py-2 rounded-lg bg-slate-800 text-white text-xs font-semibold hover:bg-slate-900"
        >
          Return to Deals
        </button>
      </div>
    );
  }

  const isPendingApproval = quotation.status === 'PENDING_APPROVAL';
  const relatedApproval = approvals.find((a: any) => a.quotation_id === quotation.id || a.status === 'PENDING') || approvals[0];
  const activeApprovalId = relatedApproval?.id;

  const handleManagerApprove = async () => {
    if (!activeApprovalId) {
      showNotification('No active approval instance found for this quote', 'warning');
      return;
    }
    try {
      await approvalService.approve(activeApprovalId, { comment: 'Approved via Quote Inspector' });
      invalidateQuote();
      showNotification('Quotation step approved by Sales Manager', 'success');
    } catch (err: any) {
      showNotification(err?.response?.data?.detail || 'Approval failed', 'error');
    }
  };

  const handleManagerRevision = async () => {
    if (!activeApprovalId) {
      showNotification('No active approval instance found for this quote', 'warning');
      return;
    }
    try {
      await approvalService.returnForRevision(activeApprovalId, { comment: 'Returned for commercial revision' });
      invalidateQuote();
      showNotification('Returned to representative for revision', 'warning');
    } catch (err: any) {
      showNotification(err?.response?.data?.detail || 'Return failed', 'error');
    }
  };

  const handleAddProduct = () => {
    if (!selectedAddProductId) return;
    addLineMutation.mutate(selectedAddProductId);
  };

  const riskScoreNum = Number(riskData?.risk_score ?? quotation.risk_score ?? 0);
  const marginPercentNum = Number(quotation.margin_percent ?? 0);
  const subtotalNum = Number(quotation.subtotal ?? 0);
  const discountAmountNum = Number(quotation.discount_amount ?? 0);
  const totalAmountNum = Number(quotation.total_amount ?? 0);
  const taxAmountNum = Number(quotation.tax_amount ?? 0);
  const orderDiscountPercentNum = Number(quotation.order_discount_percent ?? 0);

  const riskFactors: string[] = useMemo(() => {
    if (riskData?.line_risks && riskData.line_risks.length > 0) {
      const violations = riskData.line_risks
        .filter((lr: any) => lr.is_violation || Number(lr.discount_excess_percent ?? 0) > 0)
        .map((lr: any) => `${lr.product_name || 'Line item'}: Discount exceeds ceiling by ${Number(lr.discount_excess_percent ?? 0)}% (${lr.resolution_summary || 'Policy breach'})`);
      if (violations.length > 0) return violations;
    }
    if ((riskData as any)?.reasons && (riskData as any).reasons.length > 0) return (riskData as any).reasons;
    if (quotation.risk_reasons && quotation.risk_reasons.length > 0) return quotation.risk_reasons;
    return [];
  }, [riskData, quotation]);

  return (
    <div className="flex flex-col lg:flex-row gap-6 p-8 max-w-7xl mx-auto w-full flex-1">
      {/* LEFT / MAIN AREA: Quote details & product lines */}
      <div className="flex-1 space-y-6">

        {/* Manager Action Banner if pending */}
        {currentUser.role === 'SALES_MANAGER' && isPendingApproval && (
          <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 flex items-center justify-between gap-4 text-xs shadow-xs">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-purple-600 text-white flex items-center justify-center font-bold">
                <Lock className="w-5 h-5" />
              </div>
              <div>
                <span className="font-bold text-purple-950 block">Quotation In Governance Review Queue</span>
                <span className="text-purple-800">
                  Discounts exceed standard policy thresholds. Your sign-off is required to proceed.
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={handleManagerRevision}
                className="px-3 py-1.5 rounded-lg border border-purple-300 bg-white hover:bg-purple-50 text-purple-800 font-semibold transition"
              >
                Request Revision
              </button>
              <button
                onClick={handleManagerApprove}
                className="flex items-center gap-1 px-3.5 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-bold shadow-xs transition"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Approve Step</span>
              </button>
            </div>
          </div>
        )}

        {/* Rep Notice if locked in approval */}
        {currentUser.role === 'SALES_REP' && isPendingApproval && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center gap-3 text-xs shadow-xs">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <div>
              <span className="font-bold text-amber-900">Quotation Locked in Governance Queue:</span>{' '}
              <span className="text-amber-800">
                You submitted this quotation for review because commercial discounts exceed policy limits.
              </span>
            </div>
          </div>
        )}

        {/* Quote Header Card */}
        <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-xs">
          <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-gray-100">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center text-[#2563EB] font-bold">
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-[#111827] tracking-tight">{quotation.quotation_number}</h2>
                  <StatusBadge status={quotation.status} />
                  {quotation.customer_tier_name && (
                    <span className="text-xs px-2.5 py-0.5 rounded-full bg-gray-100 text-gray-700 font-medium">
                      Tier: <strong className="font-semibold text-gray-900">{quotation.customer_tier_name}</strong>
                    </span>
                  )}
                </div>
                
                <div className="text-xs text-gray-500 flex flex-wrap items-center gap-2 mt-1.5">
                  <span className="font-semibold text-gray-800">{quotation.customer_name || 'Account'}</span>
                  <span>•</span>
                  <span>Rep: {quotation.sales_rep_name || 'Sales Rep'}</span>
                  <span>•</span>
                  <span>Created: {quotation.created_at ? new Date(quotation.created_at).toLocaleDateString() : ''}</span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => recalculateMutation.mutate()}
                disabled={recalculateMutation.isPending}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 text-xs font-medium text-gray-700 transition cursor-pointer disabled:opacity-50"
                title="Recalculate pricing & discount ceilings"
              >
                <RotateCcw className={`w-3.5 h-3.5 text-gray-500 ${recalculateMutation.isPending ? 'animate-spin' : ''}`} />
                <span>Recalculate</span>
              </button>
              <button
                onClick={() => setCurrentPage('quotations')}
                className="px-3 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 text-xs font-medium text-gray-700 transition cursor-pointer"
              >
                Back to Deals
              </button>
            </div>
          </div>

          {/* Key Deal Metrics Ribbon */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4">
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">Net Subtotal</p>
              <p className="text-xl font-bold text-[#111827] font-mono mt-1">${subtotalNum.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">Total Discounts</p>
              <p className="text-xl font-bold text-emerald-700 font-mono mt-1">-${discountAmountNum.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">Order Discount</p>
              <p className="text-xl font-bold text-purple-700 font-mono mt-1">{orderDiscountPercentNum}%</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">Blended Margin</p>
              <div className="flex items-center gap-1.5 mt-1">
                <span className={`text-xl font-bold font-mono ${
                  marginPercentNum >= 35 ? 'text-green-600' : marginPercentNum >= 25 ? 'text-amber-600' : 'text-red-600'
                }`}>
                  {marginPercentNum.toFixed(1)}%
                </span>
                <TrendingUp className="w-4 h-4 text-green-500" />
              </div>
            </div>
          </div>
        </div>

        {/* Product Lines Card */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-xs overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShoppingBag className="w-4 h-4 text-[#2563EB]" />
              <h3 className="text-sm font-bold text-gray-800">Commercial Lines ({lines.length})</h3>
            </div>

            {/* Quick Add Product */}
            {quotation.status === 'DRAFT' && (
              <div className="flex items-center gap-2">
                <select
                  value={selectedAddProductId}
                  onChange={(e) => setSelectedAddProductId(e.target.value)}
                  className="text-xs bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-1.5 text-gray-700 font-medium focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
                >
                  <option value="">Select product to add...</option>
                  {products.map(p => (
                    <option key={p.id} value={p.id}>
                      {p.name} (${Number(p.list_price || 0).toLocaleString()})
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleAddProduct}
                  disabled={!selectedAddProductId || addLineMutation.isPending}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[#2563EB] hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-semibold transition shadow-xs cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Line</span>
                </button>
              </div>
            )}
          </div>

          {/* Products Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100 text-gray-500 uppercase tracking-wider font-semibold text-[11px]">
                  <th className="py-3 px-5">Item & SKU</th>
                  <th className="py-3 px-3">Type</th>
                  <th className="py-3 px-3">Unit Price</th>
                  {currentUser.role === 'FINANCE_OPERATIONS' && (
                    <th className="py-3 px-3 text-emerald-800">Unit Cost</th>
                  )}
                  <th className="py-3 px-3">Quantity</th>
                  <th className="py-3 px-3">Line Discount</th>
                  <th className="py-3 px-3">Line Total</th>
                  <th className="py-3 px-3">Margin</th>
                  <th className="py-3 px-5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {lines.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-gray-400 text-xs">
                      No commercial lines added yet. Select a product above to initialize the quotation.
                    </td>
                  </tr>
                ) : (
                  lines.map((line: QuotationLineResponse) => {
                    const excessDiscount = Number(line.discount_excess_percent ?? 0);
                    const hasViolation = excessDiscount > 0;
                    const unitPriceNum = Number(line.unit_price || 0);
                    const lineTotalNum = Number(line.line_total || 0);
                    const lineMarginNum = Number(line.margin_percent || 0);
                    const quantityNum = Number(line.quantity || 1);
                    const discountPercentNum = Number(line.discount_percent || 0);

                    return (
                      <tr key={line.id} className={`hover:bg-gray-50 transition ${hasViolation ? 'bg-red-50/20' : ''}`}>
                        <td className="py-4 px-5">
                          <div className="font-bold text-gray-900">{line.product_name || 'Product'}</div>
                          <div className="text-[11px] text-gray-400 font-mono">{line.product_sku || line.category_name || ''}</div>
                          {hasViolation && (
                            <div className="flex items-center gap-1 text-[10px] text-red-600 font-medium mt-1">
                              <AlertTriangle className="w-3 h-3 text-red-500" />
                              <span>Discount ({discountPercentNum}%) exceeds ceiling ({Number(line.allowed_discount_percent ?? line.allowed_discount_ceiling ?? 0)}%)</span>
                            </div>
                          )}
                        </td>

                        <td className="py-4 px-3">
                          {line.is_subscription ? (
                            <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-[10px] font-bold uppercase tracking-tight">
                              Recurring
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-600 text-[10px] font-medium uppercase tracking-tight">
                              One-Time
                            </span>
                          )}
                        </td>

                        <td className="py-4 px-3 font-mono font-medium text-gray-700">
                          ${unitPriceNum.toLocaleString()}
                        </td>

                        {currentUser.role === 'FINANCE_OPERATIONS' && (
                          <td className="py-4 px-3 font-mono text-emerald-700 font-semibold">
                            ${Number(line.cost_price || 0).toLocaleString()}
                          </td>
                        )}

                        <td className="py-4 px-3">
                          {quotation.status === 'DRAFT' ? (
                            <div className="inline-flex items-center border border-gray-200 rounded-md bg-white">
                              <button
                                onClick={() => {
                                  if (quantityNum > 1) {
                                    updateLineMutation.mutate({ lineId: line.id, payload: { quantity: quantityNum - 1 } });
                                  }
                                }}
                                className="px-2 py-1 text-gray-500 hover:bg-gray-100 rounded-l transition cursor-pointer"
                              >
                                -
                              </button>
                              <span className="px-3 py-1 font-mono font-bold text-gray-800 text-xs">
                                {quantityNum}
                              </span>
                              <button
                                onClick={() => {
                                  updateLineMutation.mutate({ lineId: line.id, payload: { quantity: quantityNum + 1 } });
                                }}
                                className="px-2 py-1 text-gray-500 hover:bg-gray-100 rounded-r transition cursor-pointer"
                              >
                                +
                              </button>
                            </div>
                          ) : (
                            <span className="font-mono font-bold text-gray-800">{quantityNum}</span>
                          )}
                        </td>

                        <td className="py-4 px-3">
                          {quotation.status === 'DRAFT' ? (
                            <div className="flex items-center gap-1.5">
                              <input
                                key={`${line.id}_${discountPercentNum}`}
                                type="number"
                                min="0"
                                max="100"
                                defaultValue={discountPercentNum}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter') {
                                    (e.target as HTMLInputElement).blur();
                                  }
                                }}
                                onBlur={(e) => {
                                  const val = parseFloat(e.target.value) || 0;
                                  if (val !== discountPercentNum) {
                                    updateLineMutation.mutate({ lineId: line.id, payload: { discount_percent: val } });
                                  }
                                }}
                                className={`w-14 px-2 py-1 text-xs border rounded-md font-mono font-semibold focus:outline-hidden ${
                                  hasViolation 
                                    ? 'border-red-400 bg-red-50 text-red-800' 
                                    : 'border-gray-200 bg-gray-50 text-gray-800'
                                }`}
                              />
                              <span className="text-gray-500 font-mono">%</span>
                            </div>
                          ) : (
                            <span className="font-mono font-medium text-gray-700">{discountPercentNum}%</span>
                          )}
                          {(line.allowed_discount_percent !== undefined || line.allowed_discount_ceiling !== undefined) && (
                            <span className="text-[10px] text-gray-400 block mt-0.5 font-mono">
                              Limit: {Number(line.allowed_discount_percent ?? line.allowed_discount_ceiling)}%
                            </span>
                          )}
                        </td>

                        <td className="py-4 px-3 font-mono font-bold text-gray-900">
                          ${lineTotalNum.toLocaleString()}
                        </td>

                        <td className="py-4 px-3">
                          <span className={`font-mono font-bold ${
                            lineMarginNum >= 35 ? 'text-green-600' : lineMarginNum >= 20 ? 'text-amber-600' : 'text-red-600'
                          }`}>
                            {lineMarginNum.toFixed(1)}%
                          </span>
                        </td>

                        <td className="py-4 px-5 text-right">
                          {quotation.status === 'DRAFT' && (
                            <button
                              onClick={() => deleteLineMutation.mutate(line.id)}
                              className="p-1 text-gray-400 hover:text-red-600 rounded transition cursor-pointer"
                              title="Remove Line"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pricing Calculation Summary Footer */}
          <div className="p-5 bg-gray-50 border-t border-gray-100 flex flex-col sm:flex-row items-end justify-between gap-6">
            <div className="text-xs text-gray-500 max-w-sm">
              <span className="font-semibold text-gray-700">Governance Engine Note:</span> Both line discounts and order-level discounts roll into blended deal margin. Customer tier and product category discount ceilings are enforced.
            </div>

            <div className="w-full sm:w-80 space-y-2 text-xs font-medium">
              <div className="flex justify-between text-gray-600 pt-1">
                <span>Total Commercial Discounts:</span>
                <span className="font-mono text-emerald-700">-${discountAmountNum.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Net Subtotal:</span>
                <span className="font-mono">${subtotalNum.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Estimated Tax:</span>
                <span className="font-mono">${taxAmountNum.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm font-bold text-gray-900 pt-2 border-t border-gray-200">
                <span>Total Contract Payable:</span>
                <span className="font-mono text-[#2563EB] text-base">${totalAmountNum.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Actions Bar */}
        <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-xs flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => showNotification('Draft state synchronized with server', 'info')}
              className="px-4 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 text-gray-700 text-xs font-semibold transition cursor-pointer"
            >
              Saved
            </button>
            <button
              onClick={() => sendMutation.mutate()}
              disabled={sendMutation.isPending || quotation.status === 'PENDING_APPROVAL'}
              className="px-4 py-2 rounded-lg border border-blue-200 bg-blue-50/50 hover:bg-blue-100/70 text-[#2563EB] text-xs font-semibold transition cursor-pointer disabled:opacity-50"
            >
              Send to Customer
            </button>
            <button
              onClick={() => setShowAuditTrail(!showAuditTrail)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 text-gray-600 text-xs font-medium transition cursor-pointer"
            >
              <History className="w-3.5 h-3.5 text-gray-500" />
              <span>Audit Trail</span>
              {showAuditTrail ? <ChevronUp className="w-3 h-3 ml-1" /> : <ChevronDown className="w-3 h-3 ml-1" />}
            </button>
          </div>

          <div className="flex items-center gap-2">
            {/* Sales Rep Actions */}
            {quotation.status === 'DRAFT' && (
              <button
                onClick={() => submitMutation.mutate()}
                disabled={submitMutation.isPending}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Submit for Evaluation</span>
              </button>
            )}

            {isPendingApproval && (
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
                <Lock className="w-3.5 h-3.5 text-amber-600" />
                <span>Under Approval Review</span>
              </div>
            )}

            {(quotation.status === 'APPROVED' || quotation.status === 'SENT') && (
              <button
                onClick={() => confirmMutation.mutate()}
                disabled={confirmMutation.isPending}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer disabled:opacity-50"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Confirm Order</span>
              </button>
            )}
          </div>
        </div>

        {/* Expandable Quotation Audit History */}
        {showAuditTrail && (
          <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-gray-100">
              <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider flex items-center gap-1.5">
                <History className="w-4 h-4 text-gray-500" />
                <span>Quotation Audit History</span>
              </h4>
              <span className="text-[11px] text-gray-400 font-mono">{auditLogs.length} events</span>
            </div>

            {auditLogs.length === 0 ? (
              <p className="text-xs text-gray-400">No previous audit entries logged for this quotation.</p>
            ) : (
              <div className="space-y-2 text-xs divide-y divide-gray-50 max-h-60 overflow-y-auto">
                {auditLogs.map((log: any, idx: number) => (
                  <div key={log.id || idx} className="pt-2 first:pt-0">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-bold text-gray-800">{log.action || log.event_type || 'Update'}</span>
                      <span className="text-gray-400 font-mono">
                        {log.created_at ? new Date(log.created_at).toLocaleString() : ''}
                      </span>
                    </div>
                    <div className="text-gray-600 text-[11px] mt-0.5">
                      {log.details || log.comment || log.reason || JSON.stringify(log.payload || '')}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* RIGHT SIDE PANEL: "DealFlow Intelligence" dark card */}
      <div className="w-full lg:w-96 shrink-0 space-y-6">
        <div className="bg-[#111827] text-white rounded-xl shadow-xl p-6 flex flex-col border border-slate-800">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <div className="p-1.5 bg-blue-600 rounded-md">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="text-sm font-bold tracking-wide uppercase text-white">DealFlow Intelligence</h3>
                <span className="text-[10px] text-slate-400 font-mono">Governance Engine</span>
              </div>
            </div>
            <RiskBadge score={riskScoreNum} status={riskData?.risk_status || quotation.risk_status || 'LOW_RISK'} />
          </div>

          {/* Risk Score & Meter */}
          <div className="p-4 rounded-lg bg-slate-800/60 border border-slate-700 mb-5">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="font-semibold text-slate-300">Blended Risk Score</span>
              <span className="font-mono font-bold text-white text-sm">{riskScoreNum} / 100</span>
            </div>
            <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${
                  riskScoreNum >= 60 ? 'bg-red-500' : riskScoreNum >= 30 ? 'bg-amber-500' : 'bg-green-500'
                }`}
                style={{ width: `${Math.min(100, Math.max(0, riskScoreNum))}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-slate-400 mt-2 font-mono">
              <span>0 (Healthy)</span>
              <span>30 (Manager)</span>
              <span>60 (Finance)</span>
              <span>100</span>
            </div>
          </div>

          {/* Risk Factors / Governance Reasons */}
          <div className="mb-5">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2.5 flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-slate-400" />
              <span>Risk Factors & Breaches</span>
            </div>
            <div className="space-y-2">
              {riskFactors.length === 0 ? (
                <div className="p-3 rounded-lg bg-slate-800/30 border border-slate-700/60 text-xs text-slate-400">
                  No risk breaches detected. Deal is within policy ceilings.
                </div>
              ) : (
                riskFactors.map((reason: string, idx: number) => (
                  <div key={idx} className="p-3 rounded-lg bg-slate-800/50 border border-slate-700 text-xs text-slate-200 flex items-start gap-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0 mt-0.5" />
                    <span className="leading-snug">{reason}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Automated Approval Routing Result */}
          <div className="p-4 rounded-lg border border-blue-500/30 bg-blue-500/10 mb-2">
            <div className="text-[10px] font-bold text-blue-400 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>Approval Routing Level</span>
              <span className="font-mono text-blue-300">Authoritative</span>
            </div>

            {riskData?.approval_required ? (
              <div className="flex items-center gap-2 mt-2">
                <span className="px-2.5 py-1 rounded bg-blue-600 text-white font-bold text-xs shadow-xs">
                  {riskData.required_approval_level || (riskData as any).approval_level || quotation.current_approval_level || quotation.approval_level || 'Required'}
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 text-xs text-green-400 font-semibold mt-1">
                <CheckCircle2 className="w-4 h-4 text-green-400" />
                <span>No Approval Required (Within policy limits)</span>
              </div>
            )}

            <p className="text-[11px] text-slate-300 mt-2.5 leading-relaxed">
              Discounts, margin thresholds, and customer tiers are validated server-side against backend governance policies.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
