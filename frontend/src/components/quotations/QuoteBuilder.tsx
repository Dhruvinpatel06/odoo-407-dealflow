import React, { useState } from 'react';
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
  Layers, 
  RotateCcw, 
  Send, 
  Check, 
  Info,
  Calendar,
  DollarSign,
  Zap,
  ShoppingBag,
  UserCheck,
  Lock,
  FileCheck,
  MessageSquare,
  History,
  X,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/StatusBadge';
import { RiskBadge } from '../common/RiskBadge';

export const QuoteBuilder: React.FC = () => {
  const { 
    activeQuotation, 
    customers,
    products, 
    updateLineQuantity, 
    updateLineDiscount, 
    updateOrderDiscount,
    updateActiveQuoteCustomer,
    addProductToActiveQuote, 
    removeLineFromQuote, 
    addRecommendationToQuote, 
    dismissRecommendation, 
    recommendations, 
    recalculateActiveQuote,
    saveDraftQuote,
    sendQuoteToCustomer,
    submitActiveQuoteForApproval,
    confirmActiveQuote,
    setCurrentPage,
    currentUser,
    approvals,
    negotiations,
    respondToNegotiation,
    approveCurrentStep,
    returnForRevision,
    auditLogs,
    governanceConfig,
    showNotification
  } = useApp();

  const [selectedAddProductId, setSelectedAddProductId] = useState<string>('');
  const [repCounterDiscount, setRepCounterDiscount] = useState<number>(10);
  const [repResponseNotes, setRepResponseNotes] = useState<string>('Revised hardware concession paired with standard SLA terms.');
  const [isCounterModalOpen, setIsCounterModalOpen] = useState(false);
  const [showAuditTrail, setShowAuditTrail] = useState(false);

  if (!activeQuotation) {
    return (
      <div className="p-8 text-center text-slate-500">
        No quotation selected.
      </div>
    );
  }

  // Find related approval workflow if active
  const relatedApproval = approvals.find(a => a.quotationId === activeQuotation.id);
  const isPendingApproval = activeQuotation.stage === 'PENDING_APPROVAL';
  const hasActiveNegotiation = activeQuotation.hasActiveNegotiation || activeQuotation.stage === 'UNDER_NEGOTIATION';
  const relatedNegotiation = negotiations.find(n => n.quotationId === activeQuotation.id);

  const quoteAuditLogs = auditLogs.filter(a => a.entityId === activeQuotation.id || (relatedApproval && a.entityId === relatedApproval.id));

  const handleManagerApprove = () => {
    if (relatedApproval) {
      approveCurrentStep(relatedApproval.id, 'Approved by Sales Manager via Quote Inspector.');
    } else {
      showNotification('Approved by Sales Manager.', 'success');
    }
  };

  const handleManagerRevision = () => {
    if (relatedApproval) {
      returnForRevision(relatedApproval.id, 'Returned by Sales Manager: Concession requires 2-year SaaS commitment.');
    } else {
      showNotification('Returned to representative for revision.', 'warning');
    }
  };

  const handleAddProduct = () => {
    if (!selectedAddProductId) return;
    addProductToActiveQuote(selectedAddProductId);
    setSelectedAddProductId('');
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 p-8 max-w-7xl mx-auto w-full flex-1">
      {/* LEFT / MAIN AREA: Quote details & product lines */}
      <div className="flex-1 space-y-6">
        
        {/* Customer Negotiation Response Banner for Sales Rep (Bug F fix) */}
        {hasActiveNegotiation && (
          <div className="bg-gradient-to-r from-purple-50 via-indigo-50 to-purple-50 border border-purple-200 rounded-xl p-4 shadow-sm space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-purple-600 text-white flex items-center justify-center font-bold shadow-2xs">
                  <MessageSquare className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-xs font-bold text-purple-950 flex items-center gap-2">
                    <span>Customer Negotiation Request Pending Review</span>
                    <span className="bg-purple-200 text-purple-900 text-[10px] px-2 py-0.5 rounded-full font-bold">Action Required</span>
                  </div>
                  <p className="text-[11px] text-purple-800 mt-0.5">
                    Customer proposed <strong>{relatedNegotiation?.requestedDiscountPercent ?? 18}% discount</strong> on deliverables.
                    {relatedNegotiation?.notes && <span> Note: &ldquo;{relatedNegotiation.notes}&rdquo;</span>}
                  </p>
                </div>
              </div>

              {/* Rep Response Actions */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => respondToNegotiation(activeQuotation.id, 'DECLINE', undefined, 'Original commercial parameters maintained.')}
                  className="px-3 py-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold transition cursor-pointer"
                >
                  Decline Terms
                </button>
                <button
                  onClick={() => setIsCounterModalOpen(true)}
                  className="px-3 py-1.5 rounded-lg border border-purple-300 bg-white hover:bg-purple-50 text-purple-800 text-xs font-semibold transition cursor-pointer"
                >
                  Counter-Offer
                </button>
                <button
                  onClick={() => respondToNegotiation(activeQuotation.id, 'ACCEPT', relatedNegotiation?.requestedDiscountPercent ?? 18, 'Accepted customer terms. Re-routing through discount governance.')}
                  className="px-3.5 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-xs transition cursor-pointer"
                >
                  Accept Terms
                </button>
              </div>
            </div>

            {/* Line-level customer inquiries */}
            {relatedNegotiation?.lineComments && relatedNegotiation.lineComments.length > 0 && (
              <div className="pt-2 border-t border-purple-200/60 text-xs text-purple-900 space-y-1">
                <span className="font-semibold block text-[11px]">Customer Line Inquiries:</span>
                {relatedNegotiation.lineComments.map((lc, idx) => (
                  <div key={idx} className="bg-white/80 p-2 rounded border border-purple-200/70 text-[11px]">
                    <strong>{lc.productName || 'Line Item'}:</strong> {lc.comment}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Manager Sign-Off Desk Banner */}
        {currentUser.role === 'SALES_MANAGER' && isPendingApproval && (
          <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3 shadow-2xs">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-purple-600 text-white flex items-center justify-center font-bold">
                <UserCheck className="w-5 h-5" />
              </div>
              <div>
                <div className="text-xs font-bold text-purple-900 flex items-center gap-2">
                  <span>Sales Manager Review Desk &bull; Level 1 Action Required</span>
                  <span className="bg-purple-200 text-purple-800 text-[10px] px-2 py-0.5 rounded-full font-bold">L1 Approver</span>
                </div>
                <p className="text-[11px] text-purple-700 mt-0.5">
                  Submitted by {activeQuotation.salesRepName}. Concessions exceed standard tier ceiling ({activeQuotation.customerTier}).
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleManagerRevision}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-800 text-xs font-semibold transition cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5 text-amber-600" />
                <span>Return for Revision</span>
              </button>
              <button
                onClick={handleManagerApprove}
                className="flex items-center gap-1 px-3.5 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-2xs transition cursor-pointer"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Approve as Manager (L1)</span>
              </button>
            </div>
          </div>
        )}

        {/* Rep Notice if locked in approval */}
        {currentUser.role === 'SALES_REP' && isPendingApproval && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center gap-3 text-xs shadow-2xs">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <div>
              <span className="font-bold text-amber-900">Quotation Locked in Governance Queue:</span>{' '}
              <span className="text-amber-800">
                You submitted this quotation for review because discounts exceed the {activeQuotation.customerTier} tier ceiling. 
                {activeQuotation.currentApprovalStep === 'FINANCE' ? ' Step 1 Approved by Manager. Pending Tier-2 Finance sign-off.' : ' Marcus Vance (Sales Manager) is assigned for Level 1 sign-off.'}
              </span>
            </div>
          </div>
        )}

        {/* Quote Header Card */}
        <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-gray-100">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center text-[#2563EB] font-bold">
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-[#111827] tracking-tight">{activeQuotation.quoteNumber}</h2>
                  <StatusBadge status={activeQuotation.stage} />
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-gray-100 text-gray-700 font-medium">
                    Tier: <strong className="font-semibold text-gray-900">{activeQuotation.customerTier}</strong> (Limit: {governanceConfig.tierDiscountCeilings[activeQuotation.customerTier]}%)
                  </span>
                </div>
                
                {/* Editable Customer on Draft Quotes */}
                <div className="text-xs text-gray-500 flex flex-wrap items-center gap-2 mt-1.5">
                  {activeQuotation.stage === 'DRAFT' ? (
                    <div className="flex items-center gap-1.5 bg-gray-50 border border-gray-200 rounded px-2 py-0.5">
                      <span className="font-semibold text-gray-700">Account:</span>
                      <select
                        value={activeQuotation.customerId}
                        onChange={(e) => updateActiveQuoteCustomer(e.target.value)}
                        className="bg-transparent font-bold text-blue-700 cursor-pointer focus:outline-hidden"
                      >
                        {customers.map(c => (
                          <option key={c.id} value={c.id}>{c.name} ({c.tier})</option>
                        ))}
                      </select>
                    </div>
                  ) : (
                    <span className="font-semibold text-gray-800">{activeQuotation.customerName}</span>
                  )}
                  <span>•</span>
                  <span>Rep: {activeQuotation.salesRepName}</span>
                  <span>•</span>
                  <span>Created: {new Date(activeQuotation.createdAt).toLocaleDateString()}</span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={recalculateActiveQuote}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 text-xs font-medium text-gray-700 transition cursor-pointer"
                title="Trigger mock governance recalculation"
              >
                <RotateCcw className="w-3.5 h-3.5 text-gray-500" />
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
              <p className="text-xl font-bold text-[#111827] font-mono mt-1">${activeQuotation.subtotal.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">Total Discounts</p>
              <p className="text-xl font-bold text-emerald-700 font-mono mt-1">-${activeQuotation.totalDiscountAmount.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">Order Discount</p>
              <p className="text-xl font-bold text-purple-700 font-mono mt-1">{activeQuotation.orderDiscountPercent}%</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">Blended Margin</p>
              <div className="flex items-center gap-1.5 mt-1">
                <span className={`text-xl font-bold font-mono ${
                  activeQuotation.blendedMarginPercent >= 35 ? 'text-green-600' : activeQuotation.blendedMarginPercent >= 25 ? 'text-amber-600' : 'text-red-600'
                }`}>
                  {activeQuotation.blendedMarginPercent}%
                </span>
                <TrendingUp className="w-4 h-4 text-green-500" />
              </div>
            </div>
          </div>
        </div>

        {/* Product Lines Card */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShoppingBag className="w-4 h-4 text-[#2563EB]" />
              <h3 className="text-sm font-bold text-gray-800">Commercial Lines ({activeQuotation.lines.length})</h3>
            </div>

            {/* Quick Add Product */}
            <div className="flex items-center gap-2">
              <select
                value={selectedAddProductId}
                onChange={(e) => setSelectedAddProductId(e.target.value)}
                className="text-xs bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-1.5 text-gray-700 font-medium focus:ring-2 focus:ring-blue-500 focus:outline-hidden"
              >
                <option value="">Select product to add...</option>
                {products.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.name} (${p.unitPrice.toLocaleString()}) — {p.category}
                  </option>
                ))}
              </select>
              <button
                onClick={handleAddProduct}
                disabled={!selectedAddProductId}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[#2563EB] hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-semibold transition shadow-xs cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Line</span>
              </button>
            </div>
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
                {activeQuotation.lines.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-gray-400 text-xs">
                      No commercial lines added yet. Select a product above to initialize the quotation.
                    </td>
                  </tr>
                ) : (
                  activeQuotation.lines.map((line) => {
                    const hasViolation = line.discountExcessPercent > 0;
                    const estimatedUnitCost = Math.round(line.unitPrice * (1 - (line.marginPercent || 35) / 100));
                    return (
                      <tr key={line.id} className={`hover:bg-gray-50 transition ${hasViolation ? 'bg-red-50/20' : ''}`}>
                        {/* Product Name & SKU */}
                        <td className="py-4 px-5">
                          <div className="font-bold text-gray-900">{line.productName}</div>
                          <div className="text-[11px] text-gray-400 font-mono">Category: {line.category}</div>
                          {hasViolation && (
                            <div className="flex items-center gap-1 text-[10px] text-red-600 font-medium mt-1">
                              <AlertTriangle className="w-3 h-3 text-red-500" />
                              <span>Discount ({line.discountPercent}%) exceeds ceiling ({line.allowedDiscountCeiling}%) by +{line.discountExcessPercent}%</span>
                            </div>
                          )}
                        </td>

                        {/* Type Pill */}
                        <td className="py-4 px-3">
                          {line.isSubscription ? (
                            <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-[10px] font-bold uppercase tracking-tight">
                              Recurring ({line.recurringInterval || 'MO'})
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-600 text-[10px] font-medium uppercase tracking-tight">
                              One-Time
                            </span>
                          )}
                        </td>

                        {/* Unit Price */}
                        <td className="py-4 px-3 font-mono font-medium text-gray-700">
                          ${line.unitPrice.toLocaleString()}
                        </td>

                        {/* Finance-Only Unit Cost */}
                        {currentUser.role === 'FINANCE_OPERATIONS' && (
                          <td className="py-4 px-3 font-mono text-emerald-700 font-semibold">
                            ${estimatedUnitCost.toLocaleString()}
                          </td>
                        )}

                        {/* Quantity Stepper */}
                        <td className="py-4 px-3">
                          <div className="inline-flex items-center border border-gray-200 rounded-md bg-white">
                            <button
                              onClick={() => updateLineQuantity(line.id, -1)}
                              className="px-2 py-1 text-gray-500 hover:bg-gray-100 rounded-l transition cursor-pointer"
                            >
                              -
                            </button>
                            <span className="px-3 py-1 font-mono font-bold text-gray-800 text-xs">
                              {line.quantity}
                            </span>
                            <button
                              onClick={() => updateLineQuantity(line.id, 1)}
                              className="px-2 py-1 text-gray-500 hover:bg-gray-100 rounded-r transition cursor-pointer"
                            >
                              +
                            </button>
                          </div>
                        </td>

                        {/* Discount % with Governance warning */}
                        <td className="py-4 px-3">
                          <div className="flex items-center gap-1.5">
                            <input
                              type="number"
                              min="0"
                              max="100"
                              value={line.discountPercent}
                              onChange={(e) => updateLineDiscount(line.id, parseFloat(e.target.value) || 0)}
                              className={`w-14 px-2 py-1 text-xs border rounded-md font-mono font-semibold focus:outline-hidden ${
                                hasViolation 
                                  ? 'border-red-400 bg-red-50 text-red-800 focus:ring-2 focus:ring-red-500' 
                                  : 'border-gray-200 bg-gray-50 text-gray-800 focus:ring-2 focus:ring-blue-500'
                              }`}
                            />
                            <span className="text-gray-500 font-mono">%</span>
                          </div>
                          <span className="text-[10px] text-gray-400 block mt-0.5 font-mono">
                            Limit: {line.allowedDiscountCeiling}%
                          </span>
                        </td>

                        {/* Line Total */}
                        <td className="py-4 px-3 font-mono font-bold text-gray-900">
                          ${line.lineTotal.toLocaleString()}
                        </td>

                        {/* Margin % */}
                        <td className="py-4 px-3">
                          <span className={`font-mono font-bold ${
                            line.marginPercent >= 35 ? 'text-green-600' : line.marginPercent >= 20 ? 'text-amber-600' : 'text-red-600'
                          }`}>
                            {line.marginPercent.toFixed(1)}%
                          </span>
                        </td>

                        {/* Delete */}
                        <td className="py-4 px-5 text-right">
                          <button
                            onClick={() => removeLineFromQuote(line.id)}
                            className="p-1 text-gray-400 hover:text-red-600 rounded transition cursor-pointer"
                            title="Remove Line"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pricing Calculation Summary Footer with ORDER-LEVEL DISCOUNT (Bug B fix) */}
          <div className="p-5 bg-gray-50 border-t border-gray-100 flex flex-col sm:flex-row items-end justify-between gap-6">
            <div className="text-xs text-gray-500 max-w-sm">
              <span className="font-semibold text-gray-700">Governance Engine Note:</span> Both line discounts and order-level discounts roll into blended deal margin. Stricter tier and category ceilings are actively evaluated.
            </div>

            <div className="w-full sm:w-80 space-y-2 text-xs font-medium">
              {/* Order-Level Discount Control */}
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-blue-50/80 border border-blue-200">
                <div>
                  <span className="font-bold text-blue-950 block">Order-Level Discount:</span>
                  <span className="text-[10px] text-blue-700 font-normal">Applies across entire commercial schedule</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <input
                    type="number"
                    min="0"
                    max="50"
                    step="0.5"
                    value={activeQuotation.orderDiscountPercent || 0}
                    onChange={(e) => updateOrderDiscount(activeQuotation.id, parseFloat(e.target.value) || 0)}
                    className="w-16 px-2 py-1 text-right font-mono font-bold bg-white border border-blue-300 rounded text-xs text-blue-900 focus:ring-1 focus:ring-blue-500 focus:outline-hidden"
                  />
                  <span className="font-mono font-bold text-blue-800">%</span>
                </div>
              </div>

              <div className="flex justify-between text-gray-600 pt-1">
                <span>Total Commercial Discounts:</span>
                <span className="font-mono text-emerald-700">-${activeQuotation.totalDiscountAmount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Net Subtotal:</span>
                <span className="font-mono">${activeQuotation.subtotal.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Estimated Tax (8%):</span>
                <span className="font-mono">${activeQuotation.taxAmount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm font-bold text-gray-900 pt-2 border-t border-gray-200">
                <span>Total Contract Payable:</span>
                <span className="font-mono text-[#2563EB] text-base">${activeQuotation.totalAmount.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Actions Bar */}
        <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={saveDraftQuote}
              className="px-4 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 text-gray-700 text-xs font-semibold transition cursor-pointer"
            >
              Save Draft
            </button>
            <button
              onClick={sendQuoteToCustomer}
              className="px-4 py-2 rounded-lg border border-blue-200 bg-blue-50/50 hover:bg-blue-100/70 text-[#2563EB] text-xs font-semibold transition cursor-pointer"
            >
              Send to Customer
            </button>
            <button
              onClick={() => setShowAuditTrail(!showAuditTrail)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 text-gray-600 text-xs font-medium transition cursor-pointer"
            >
              <History className="w-3.5 h-3.5 text-gray-500" />
              <span>Audit Trail ({quoteAuditLogs.length})</span>
              {showAuditTrail ? <ChevronUp className="w-3 h-3 ml-1" /> : <ChevronDown className="w-3 h-3 ml-1" />}
            </button>
          </div>

          <div className="flex items-center gap-2">
            {/* Sales Manager Actions */}
            {currentUser.role === 'SALES_MANAGER' && isPendingApproval && (
              <>
                <button
                  onClick={handleManagerRevision}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-800 text-xs font-semibold transition cursor-pointer"
                >
                  <RotateCcw className="w-3.5 h-3.5 text-amber-600" />
                  <span>Return for Revision</span>
                </button>
                <button
                  onClick={handleManagerApprove}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-xs transition cursor-pointer"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Approve as Manager (L1)</span>
                </button>
              </>
            )}

            {/* Sales Rep Actions */}
            {currentUser.role === 'SALES_REP' && (
              <>
                {activeQuotation.stage === 'DRAFT' && (
                  <button
                    onClick={submitActiveQuoteForApproval}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition cursor-pointer"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Submit for Governance Evaluation</span>
                  </button>
                )}

                {isPendingApproval && (
                  <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
                    <Lock className="w-3.5 h-3.5 text-amber-600" />
                    <span>Locked in Governance Approval</span>
                  </div>
                )}

                {activeQuotation.stage === 'APPROVED' && (
                  <button
                    onClick={confirmActiveQuote}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-xs font-semibold shadow-sm transition cursor-pointer"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Confirm Deal</span>
                  </button>
                )}
              </>
            )}

            {/* Admin or Finance Actions */}
            {currentUser.role !== 'SALES_MANAGER' && currentUser.role !== 'SALES_REP' && (
              <>
                <button
                  onClick={submitActiveQuoteForApproval}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition cursor-pointer"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Evaluate Approval</span>
                </button>
                <button
                  onClick={confirmActiveQuote}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-xs font-semibold shadow-sm transition cursor-pointer"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Confirm Deal</span>
                </button>
              </>
            )}
          </div>
        </div>

        {/* Expandable Quotation Audit History */}
        {showAuditTrail && (
          <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-gray-100">
              <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider flex items-center gap-1.5">
                <History className="w-4 h-4 text-gray-500" />
                <span>Quotation Audit History</span>
              </h4>
              <span className="text-[11px] text-gray-400 font-mono">{quoteAuditLogs.length} events logged</span>
            </div>

            {quoteAuditLogs.length === 0 ? (
              <p className="text-xs text-gray-400">No previous audit entries logged for this quotation.</p>
            ) : (
              <div className="space-y-2 text-xs divide-y divide-gray-50 max-h-60 overflow-y-auto">
                {quoteAuditLogs.map((log) => (
                  <div key={log.id} className="pt-2 first:pt-0">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-bold text-gray-800">{log.action.replace(/_/g, ' ')}</span>
                      <span className="text-gray-400 font-mono">{new Date(log.timestamp).toLocaleString()}</span>
                    </div>
                    <div className="text-gray-600 text-[11px] mt-0.5">
                      <strong className="text-gray-700">{log.userName}</strong> ({log.userRole}): {log.details || log.reason || 'Recorded change'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* RIGHT SIDE PANEL: "DealFlow Intelligence" matching Editorial Aesthetic signature dark card */}
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
            <RiskBadge score={activeQuotation.blendedRiskScore} status={activeQuotation.riskStatus} />
          </div>

          {/* Risk Score & Meter */}
          <div className="p-4 rounded-lg bg-slate-800/60 border border-slate-700 mb-5">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="font-semibold text-slate-300">Blended Risk Score</span>
              <span className="font-mono font-bold text-white text-sm">{activeQuotation.blendedRiskScore} / 100</span>
            </div>
            <div className="w-full h-2 rounded-full bg-slate-900 overflow-hidden">
              <div
                className={`h-full transition-all duration-300 ${
                  activeQuotation.blendedRiskScore >= governanceConfig.financeApprovalRiskThreshold
                    ? 'bg-red-500'
                    : activeQuotation.blendedRiskScore >= governanceConfig.managerApprovalRiskThreshold
                    ? 'bg-amber-500'
                    : 'bg-green-500'
                }`}
                style={{ width: `${activeQuotation.blendedRiskScore}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-slate-400 mt-2 font-mono">
              <span>0 (Healthy)</span>
              <span>{governanceConfig.managerApprovalRiskThreshold} (Manager)</span>
              <span>{governanceConfig.financeApprovalRiskThreshold} (Finance)</span>
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
              {activeQuotation.riskReasons.map((reason, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-slate-800/50 border border-slate-700 text-xs text-slate-200 flex items-start gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0 mt-0.5" />
                  <span className="leading-snug">{reason}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Automated Approval Routing Result */}
          <div className="p-4 rounded-lg border border-blue-500/30 bg-blue-500/10 mb-5">
            <div className="text-[10px] font-bold text-blue-400 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>Automated Routing Level</span>
              <span className="font-mono text-blue-300">Authoritative</span>
            </div>

            {activeQuotation.requiredApprovalLevel === 'MANAGER_AND_FINANCE' && (
              <div className="flex items-center gap-2 mt-2">
                <span className="px-2.5 py-1 rounded bg-blue-600 text-white font-bold text-xs shadow-xs">
                  Sales Manager (L1)
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-blue-400" />
                <span className="px-2.5 py-1 rounded bg-purple-600 text-white font-bold text-xs shadow-xs">
                  Finance / Ops (L2)
                </span>
              </div>
            )}

            {activeQuotation.requiredApprovalLevel === 'SALES_MANAGER' && (
              <div className="flex items-center gap-2 mt-2">
                <span className="px-2.5 py-1 rounded bg-blue-600 text-white font-bold text-xs shadow-xs">
                  Sales Manager Required
                </span>
              </div>
            )}

            {activeQuotation.requiredApprovalLevel === 'NONE' && (
              <div className="flex items-center gap-1.5 text-xs text-green-400 font-semibold mt-1">
                <CheckCircle2 className="w-4 h-4 text-green-400" />
                <span>No Approval Required (Within policy limits)</span>
              </div>
            )}

            <p className="text-[11px] text-slate-300 mt-2.5 leading-relaxed">
              Sales reps cannot manually bypass approval levels. The governance policy automatically assigns reviewers sequentially based on blended risk.
            </p>
          </div>

          {/* Upsell / Cross-sell Recommendations */}
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                <span>Smart Recommendations</span>
              </span>
              <span className="text-[10px] text-slate-500 font-normal">Margin Lift</span>
            </div>

            {recommendations.length === 0 ? (
              <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700 text-center text-xs text-slate-400">
                All available upsell suggestions added or dismissed.
              </div>
            ) : (
              <div className="space-y-3">
                {recommendations.map((rec) => (
                  <div 
                    key={rec.productId} 
                    className="p-3.5 rounded-lg border border-slate-700 bg-slate-800/50 hover:border-blue-500/40 transition"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="font-bold text-xs text-white">{rec.productName}</div>
                        <div className="text-[11px] text-slate-300 mt-1 leading-relaxed">{rec.reason}</div>
                      </div>
                      <span className="shrink-0 px-2 py-0.5 rounded bg-green-500/20 text-green-400 text-[10px] font-bold">
                        +{rec.marginDelta}% Margin
                      </span>
                    </div>

                    <div className="mt-3 pt-2 border-t border-slate-700/60 flex items-center justify-between">
                      <span className="font-mono font-bold text-xs text-slate-200">
                        ${rec.unitPrice.toLocaleString()}
                      </span>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => dismissRecommendation(rec.productId)}
                          className="px-2 py-1 text-slate-400 hover:text-white text-xs rounded transition cursor-pointer"
                        >
                          Dismiss
                        </button>
                        <button
                          onClick={() => addRecommendationToQuote(rec)}
                          className="text-[11px] bg-blue-600 hover:bg-blue-500 text-white font-medium px-3 py-1 rounded transition-colors cursor-pointer"
                        >
                          Add to Quote
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Rep Counter-Offer Modal */}
      {isCounterModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-md w-full p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900">Counter-Proposal to Customer</h3>
              <button
                onClick={() => setIsCounterModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Proposed Counter Discount (%):</label>
                <input
                  type="number"
                  min="0"
                  max="40"
                  value={repCounterDiscount}
                  onChange={(e) => setRepCounterDiscount(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 font-mono font-bold text-sm text-slate-900"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Commercial Message to Client:</label>
                <textarea
                  rows={3}
                  value={repResponseNotes}
                  onChange={(e) => setRepResponseNotes(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs"
                />
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
              <button
                onClick={() => setIsCounterModalOpen(false)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  respondToNegotiation(activeQuotation.id, 'COUNTER', repCounterDiscount, repResponseNotes);
                  setIsCounterModalOpen(false);
                }}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-purple-600 hover:bg-purple-700 rounded-lg shadow-2xs"
              >
                Dispatch Counter-Proposal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
