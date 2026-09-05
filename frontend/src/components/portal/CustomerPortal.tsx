import React, { useState } from 'react';
import { 
  Building2, 
  CheckCircle2, 
  Send, 
  MessageSquare, 
  DollarSign, 
  ShieldCheck, 
  ArrowLeft, 
  HelpCircle,
  FileText,
  Clock,
  ExternalLink
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/StatusBadge';

export const CustomerPortal: React.FC = () => {
  const { 
    quotations, 
    submitCustomerNegotiation, 
    customerConfirmQuote, 
    setUserRole, 
    setCurrentPage,
    showNotification 
  } = useApp();

  const [counterDiscount, setCounterDiscount] = useState<number>(18);
  const [changeReason, setChangeReason] = useState<string>('We require an additional 4% concession on the compute server lines to match our board capital expenditure budget.');
  const [lineComment, setLineComment] = useState<string>('');

  // Target quotation for customer portal demo (Q-1049 NovaTech or Q-1048 Acme)
  const [activeQuoteId, setActiveQuoteId] = useState<string>('q-1049');
  const quote = quotations.find(q => q.id === activeQuoteId) || quotations[0];

  const handleConfirm = () => {
    customerConfirmQuote(quote.id);
  };

  const handleNegotiate = (e: React.FormEvent) => {
    e.preventDefault();
    submitCustomerNegotiation(quote.id, counterDiscount, changeReason);
  };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 pb-12">
      {/* Customer Portal Top Nav (Visually distinct from internal admin!) */}
      <nav className="bg-white border-b border-slate-200 px-6 py-3.5 shadow-2xs">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center font-bold shadow-xs">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <span className="font-bold text-slate-900 tracking-tight text-base">DealFlow360</span>
              <span className="text-slate-400 text-xs ml-2 font-medium">Customer Collaboration Portal</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-bold text-slate-900">{quote.customerName}</div>
              <div className="text-[11px] text-slate-500">Verified Client Account</div>
            </div>
            <button
              onClick={() => {
                setUserRole('SALES_REP');
                setCurrentPage('dashboard');
              }}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Return to Internal Sales Workspace</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Main Container */}
      <div className="max-w-4xl mx-auto px-4 pt-8 space-y-6">
        {/* Proposal Header Banner */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                  Quotation Proposal: {quote.quoteNumber}
                </h1>
                <StatusBadge status={quote.stage} />
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Prepared exclusively for <strong className="text-slate-800">{quote.customerName}</strong> by {quote.salesRepName}.
              </p>
            </div>

            {/* Negotiation Status Indicator */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">Negotiation State:</span>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200">
                Live Interactive Review
              </span>
            </div>
          </div>

          {/* Customer Quote Notice (Restricted Information Boundary) */}
          <div className="mt-4 p-3.5 rounded-lg bg-emerald-50/80 border border-emerald-200 text-emerald-950 text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>
                <strong>Confidential Client Access:</strong> You are viewing verified client terms. Internal cost structures, company margins, and risk governance routes are strictly quarantined.
              </span>
            </div>
            <span className="text-[10px] font-mono font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded shrink-0">
              RBAC Privacy Active
            </span>
          </div>
        </div>

        {/* Commercial Items Table (NO INTERNAL MARGINS OR RISK CALCULATIONS SHOWN!) */}
        <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden">
          <div className="p-5 border-b border-slate-100">
            <h2 className="text-sm font-bold text-slate-900">Commercial Schedule & Deliverables</h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[10px]">
                  <th className="py-3 px-5">Description</th>
                  <th className="py-3 px-3">Billing Type</th>
                  <th className="py-3 px-3 text-center">Qty</th>
                  <th className="py-3 px-3">List Price</th>
                  <th className="py-3 px-3">Agreed Discount</th>
                  <th className="py-3 px-5 text-right">Line Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {quote.lines.map((line) => (
                  <tr key={line.id} className="hover:bg-slate-50/60 transition">
                    <td className="py-4 px-5">
                      <div className="font-semibold text-slate-900 text-sm">{line.productName}</div>
                      <div className="text-[11px] text-slate-400">Class: {line.category}</div>
                    </td>
                    <td className="py-4 px-3">
                      {line.isSubscription ? (
                        <span className="px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 text-[10px] font-medium">
                          Monthly Subscription
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 text-[10px] font-medium">
                          One-Time Delivery
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-3 text-center font-mono font-bold text-slate-800">
                      {line.quantity}
                    </td>
                    <td className="py-4 px-3 font-mono text-slate-600">
                      ${line.unitPrice.toLocaleString()}
                    </td>
                    <td className="py-4 px-3">
                      <span className="font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                        {line.discountPercent}% Off
                      </span>
                    </td>
                    <td className="py-4 px-5 text-right font-mono font-bold text-slate-900 text-sm">
                      ${line.lineTotal.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pricing Total Summary */}
          <div className="p-6 bg-slate-50/70 border-t border-slate-200 flex flex-col sm:flex-row items-end justify-between gap-4">
            <div className="text-xs text-slate-500 max-w-sm">
              Standard commercial terms apply. All pricing valid for 30 days from proposal date.
            </div>
            <div className="w-full sm:w-72 space-y-1.5 text-xs font-medium">
              <div className="flex justify-between text-slate-600">
                <span>Gross Amount:</span>
                <span className="font-mono">${(quote.subtotal + quote.totalDiscountAmount).toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-emerald-700">
                <span>Contract Discount:</span>
                <span className="font-mono">-${quote.totalDiscountAmount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Estimated Tax:</span>
                <span className="font-mono">${quote.taxAmount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-base font-bold text-slate-900 pt-2 border-t border-slate-200">
                <span>Total Payable:</span>
                <span className="font-mono text-emerald-700">${quote.totalAmount.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Interactive Negotiation & Counter Proposal Panel */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-xs space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-blue-600" />
              <h3 className="text-sm font-bold text-slate-900">Negotiate Terms or Request Changes</h3>
            </div>
            <span className="text-xs text-slate-400">Direct Sales Channel</span>
          </div>

          <form onSubmit={handleNegotiate} className="space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Proposed Counter Discount on Primary Line (%):
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  min="0"
                  max="50"
                  value={counterDiscount}
                  onChange={(e) => setCounterDiscount(parseFloat(e.target.value) || 0)}
                  className="w-24 px-3 py-2 border border-slate-300 rounded-lg font-mono font-bold text-sm bg-slate-50 focus:bg-white focus:ring-1 focus:ring-blue-500"
                />
                <span className="text-slate-500 text-xs">
                  (e.g., Requesting 18% counter-discount will trigger automatic re-approval governance on the sales side)
                </span>
              </div>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">
                Comments, Questions or Commercial Justification:
              </label>
              <textarea
                rows={3}
                value={changeReason}
                onChange={(e) => setChangeReason(e.target.value)}
                placeholder="Explain the reason for counter proposal or ask line-level questions..."
                className="w-full p-3 rounded-lg border border-slate-300 bg-slate-50 focus:bg-white focus:ring-1 focus:ring-blue-500"
              />
            </div>

            {/* Actions Bar */}
            <div className="pt-2 flex flex-wrap items-center justify-between gap-3">
              <button
                type="submit"
                className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg border border-blue-300 bg-blue-50 hover:bg-blue-100 text-blue-800 font-semibold text-xs transition cursor-pointer"
              >
                <Send className="w-3.5 h-3.5 text-blue-600" />
                <span>Submit Negotiation Request</span>
              </button>

              <button
                type="button"
                onClick={handleConfirm}
                className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-sm transition cursor-pointer"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Confirm & Accept Final Terms</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
