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
  FileCheck
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/StatusBadge';
import { RiskBadge } from '../common/RiskBadge';

export const QuoteBuilder: React.FC = () => {
  const { 
    activeQuotation, 
    products, 
    updateLineQuantity, 
    updateLineDiscount, 
    addProductToActiveQuote, 
    removeLineFromQuote, 
    addRecommendationToQuote, 
    dismissRecommendation, 
    recommendations, 
    recalculateActiveQuote,
    submitActiveQuoteForApproval,
    confirmActiveQuote,
    setCurrentPage,
    currentUser,
    approvals,
    approveCurrentStep,
    returnForRevision,
    showNotification
  } = useApp();

  const [selectedAddProductId, setSelectedAddProductId] = useState<string>('');

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
                Marcus Vance (Sales Manager) has been assigned for Level 1 sign-off.
              </span>
            </div>
          </div>
        )}

        {/* Finance Context Banner */}
        {currentUser.role === 'FINANCE_OPERATIONS' && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3.5 flex items-center justify-between gap-3 text-xs">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
              <span className="font-bold text-emerald-950">Finance & RevOps View:</span>
              <span className="text-emerald-800">Unit COGS margins and gross profitability floor (30%) are actively tracked.</span>
            </div>
            <span className="font-mono text-[11px] font-bold text-emerald-900 bg-emerald-100 px-2 py-0.5 rounded">
              Blended Margin: {activeQuotation.blendedMarginPercent}%
            </span>
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
                    Tier: <strong className="font-semibold text-gray-900">{activeQuotation.customerTier}</strong> (Ceiling: {activeQuotation.customerTier === 'GOLD' ? '15%' : activeQuotation.customerTier === 'SILVER' ? '10%' : activeQuotation.customerTier === 'PLATINUM' ? '20%' : '5%'})
                  </span>
                </div>
                <div className="text-xs text-gray-500 flex items-center gap-2 mt-1">
                  <span className="font-semibold text-gray-800">{activeQuotation.customerName}</span>
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
                title="Trigger backend recalculation"
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
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">Subtotal</p>
              <p className="text-xl font-bold text-[#111827] font-mono mt-1">${activeQuotation.subtotal.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">Total Discounts</p>
              <p className="text-xl font-bold text-gray-700 font-mono mt-1">-${activeQuotation.totalDiscountAmount.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">Estimated Tax</p>
              <p className="text-xl font-bold text-gray-700 font-mono mt-1">${activeQuotation.taxAmount.toLocaleString()}</p>
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
                {activeQuotation.lines.map((line) => {
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
                })}
              </tbody>
            </table>
          </div>

          {/* Pricing Calculation Summary Footer */}
          <div className="p-5 bg-gray-50 border-t border-gray-100 flex flex-col sm:flex-row items-end justify-between gap-4">
            <div className="text-xs text-gray-500 max-w-sm">
              <span className="font-semibold text-gray-700">Governance Note:</span> Selling price, discount ceilings, and blended risk are backend-authoritative. Live totals automatically recompute margin & approval routing.
            </div>
            <div className="w-full sm:w-64 space-y-1.5 text-xs font-medium">
              <div className="flex justify-between text-gray-600">
                <span>Subtotal:</span>
                <span className="font-mono">${activeQuotation.subtotal.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Total Discount:</span>
                <span className="font-mono text-gray-700">-${activeQuotation.totalDiscountAmount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Tax (Est.):</span>
                <span className="font-mono">${activeQuotation.taxAmount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-sm font-bold text-gray-900 pt-2 border-t border-gray-200">
                <span>Total Amount:</span>
                <span className="font-mono text-[#2563EB] text-base">${activeQuotation.totalAmount.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Actions Bar */}
        <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => showNotification('Draft saved to database', 'info')}
              className="px-4 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 text-gray-700 text-xs font-semibold transition cursor-pointer"
            >
              Save Draft
            </button>
            <button
              onClick={() => {
                showNotification(`Sent Quote ${activeQuotation.quoteNumber} to customer portal`, 'success');
              }}
              className="px-4 py-2 rounded-lg border border-gray-200 hover:bg-gray-50 text-gray-700 text-xs font-semibold transition cursor-pointer"
            >
              Send to Customer
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
                    <span>Send for Approval</span>
                  </button>
                )}

                {isPendingApproval && (
                  <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
                    <Lock className="w-3.5 h-3.5 text-amber-600" />
                    <span>Locked in Approval (Marcus Vance)</span>
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

            {/* Other Roles Default / Admin / Finance */}
            {currentUser.role !== 'SALES_MANAGER' && currentUser.role !== 'SALES_REP' && (
              <>
                <button
                  onClick={submitActiveQuoteForApproval}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition cursor-pointer"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Send for Approval</span>
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
                  activeQuotation.blendedRiskScore >= 70
                    ? 'bg-red-500'
                    : activeQuotation.blendedRiskScore >= 45
                    ? 'bg-amber-500'
                    : 'bg-green-500'
                }`}
                style={{ width: `${activeQuotation.blendedRiskScore}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-slate-400 mt-2 font-mono">
              <span>0 (Low)</span>
              <span>45 (Manager)</span>
              <span>70 (Finance)</span>
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
                  Sales Manager
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-blue-400" />
                <span className="px-2.5 py-1 rounded bg-blue-600 text-white font-bold text-xs shadow-xs">
                  Finance / Ops
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
              Sales reps cannot manually pick or bypass approval levels. The governance policy automatically assigns reviewers sequentially based on risk.
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
    </div>
  );
};
