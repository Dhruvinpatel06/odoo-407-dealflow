import React, { useState } from 'react';
import {
  Building2,
  CheckCircle2,
  DollarSign,
  ShieldCheck,
  FileText,
  LogOut,
  Loader2
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/StatusBadge';
import { quotationService } from '../../services/api';
import { QuotationResponse, QuotationLineResponse } from '../../services/quotationService';

export const CustomerPortal: React.FC = () => {
  const { currentUser, setCurrentPage, showNotification } = useApp();
  const queryClient = useQueryClient();

  const [activeQuoteId, setActiveQuoteId] = useState<string>('');

  // 1. Fetch Quotations available to this customer
  const { data: quotations = [], isLoading: isQuotesLoading } = useQuery({
    queryKey: ['customer-quotations'],
    queryFn: () => quotationService.listQuotations(),
  });

  const activeQuote = quotations.find((q: QuotationResponse) => q.id === activeQuoteId) || quotations[0];
  const currentQuoteId = activeQuote?.id;

  // 2. Fetch Lines for the active quote
  const { data: lines = [], isLoading: isLinesLoading } = useQuery({
    queryKey: ['customer-quote-lines', currentQuoteId],
    queryFn: () => quotationService.getLines(currentQuoteId!),
    enabled: Boolean(currentQuoteId),
  });

  // Confirm Mutation
  const confirmMutation = useMutation({
    mutationFn: (quoteId: string) => quotationService.confirm(quoteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customer-quotations'] });
      queryClient.invalidateQueries({ queryKey: ['customer-quote-lines', currentQuoteId] });
      showNotification('Quotation confirmed! Your order has been placed into execution.', 'success');
    },
    onError: (err: any) => {
      showNotification(err?.response?.data?.detail || 'Confirmation failed.', 'error');
    },
  });

  if (isQuotesLoading) {
    return (
      <div className="min-h-screen bg-slate-100 flex flex-col items-center justify-center text-slate-500 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
        <span className="text-xs font-medium">Connecting to Customer Portal...</span>
      </div>
    );
  }

  if (!activeQuote) {
    return (
      <div className="min-h-screen bg-slate-100 text-slate-900 flex flex-col items-center justify-center p-6">
        <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-xs text-center max-w-md space-y-4">
          <Building2 className="w-10 h-10 text-slate-400 mx-auto" />
          <h2 className="text-lg font-bold text-slate-800">No Active Proposals</h2>
          <p className="text-xs text-slate-500">
            There are currently no active quotation proposals issued for your account. Please contact your dedicated account executive.
          </p>
          <button
            onClick={() => {
              setCurrentPage('login');
            }}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg border border-slate-300 text-slate-700 text-xs font-semibold hover:bg-slate-50 transition cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    );
  }

  const subtotalNum = Number(activeQuote.subtotal || 0);
  const discountNum = Number(activeQuote.discount_amount || 0);
  const totalNum = Number(activeQuote.total_amount || 0);
  const taxNum = Number(activeQuote.tax_amount || 0);

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 pb-12">
      {/* Customer Portal Top Nav */}
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

          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-bold text-slate-900">{activeQuote.customer_name || 'Customer'}</div>
              <div className="text-[11px] text-slate-500 flex items-center gap-1.5 justify-end">
                <span>Account ID: {activeQuote.customer_id?.substring(0, 8)}</span>
                {quotations.length > 1 && (
                  <select
                    value={activeQuote.id}
                    onChange={(e) => setActiveQuoteId(e.target.value)}
                    className="ml-1 bg-slate-50 border border-slate-200 rounded text-[10px] font-mono px-1 py-0.5"
                  >
                    {quotations.map((q: QuotationResponse) => (
                      <option key={q.id} value={q.id}>{q.quotation_number}</option>
                    ))}
                  </select>
                )}
              </div>
            </div>

            <button
              onClick={() => setCurrentPage('login')}
              title="Sign Out to Login Screen"
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-red-50 hover:text-red-700 hover:border-red-200 text-xs font-semibold text-slate-700 transition cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
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
                  Quotation Proposal: {activeQuote.quotation_number}
                </h1>
                <StatusBadge status={activeQuote.status} />
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Prepared exclusively for <strong className="text-slate-800">{activeQuote.customer_name || 'your organization'}</strong>.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-medium">Status:</span>
              <span className={`text-xs font-semibold px-2.5 py-1 rounded-md border ${
                activeQuote.status === 'CONFIRMED'
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                  : 'bg-blue-50 text-blue-800 border-blue-200'
              }`}>
                {activeQuote.status === 'CONFIRMED' ? 'Confirmed Order' : 'Live Proposal Review'}
              </span>
            </div>
          </div>

          <div className="mt-4 p-3.5 rounded-lg bg-emerald-50/80 border border-emerald-200 text-emerald-950 text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>
                <strong>Verified Client Account ({currentUser.name}):</strong> You are viewing terms exclusively for your account. Internal margins and governance rules are quarantined.
              </span>
            </div>
            <span className="text-[10px] font-mono font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded shrink-0">
              Customer Data Isolated
            </span>
          </div>
        </div>

        {/* Commercial Items Table */}
        <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-900">Commercial Schedule & Deliverables</h2>
            <span className="text-xs text-slate-400">{lines.length} Line Item(s)</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[10px]">
                  <th className="py-3 px-5">Description</th>
                  <th className="py-3 px-3">Billing Type</th>
                  <th className="py-3 px-3 text-center">Qty</th>
                  <th className="py-3 px-3">Unit Price</th>
                  <th className="py-3 px-3">Discount</th>
                  <th className="py-3 px-5 text-right">Line Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {lines.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400 text-xs">
                      No commercial lines found for this quote.
                    </td>
                  </tr>
                ) : (
                  lines.map((line: QuotationLineResponse) => {
                    const unitPrice = Number(line.unit_price || 0);
                    const lineTotal = Number(line.line_total || 0);
                    const discPercent = Number(line.discount_percent || 0);

                    return (
                      <tr key={line.id} className="hover:bg-slate-50/60 transition">
                        <td className="py-4 px-5">
                          <div className="font-semibold text-slate-900 text-sm">{line.product_name || 'Product'}</div>
                          <div className="text-[11px] text-slate-400">SKU: {line.product_sku || line.product_id?.substring(0, 8)}</div>
                        </td>
                        <td className="py-4 px-3">
                          {line.is_subscription ? (
                            <span className="px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 text-[10px] font-medium">
                              Recurring Subscription
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 text-[10px] font-medium">
                              One-Time Delivery
                            </span>
                          )}
                        </td>
                        <td className="py-4 px-3 text-center font-mono font-bold text-slate-800">
                          {Number(line.quantity || 1)}
                        </td>
                        <td className="py-4 px-3 font-mono text-slate-600">
                          ${unitPrice.toLocaleString()}
                        </td>
                        <td className="py-4 px-3">
                          {discPercent > 0 ? (
                            <span className="font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                              {discPercent}% Off
                            </span>
                          ) : (
                            <span className="font-mono text-slate-400">0%</span>
                          )}
                        </td>
                        <td className="py-4 px-5 text-right font-mono font-bold text-slate-900 text-sm">
                          ${lineTotal.toLocaleString()}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pricing Totals Card */}
          <div className="p-6 bg-slate-50 border-t border-slate-200 flex flex-col sm:flex-row items-end justify-between gap-6">
            <div className="text-xs text-slate-500 max-w-sm space-y-1">
              <span className="font-semibold text-slate-700 block">Commercial Acceptance Policy:</span>
              <p>
                Confirming this proposal authorizes order conversion and locks delivery terms under agreed payment provisions.
              </p>
            </div>

            <div className="w-full sm:w-80 space-y-2 text-xs font-medium">
              <div className="flex justify-between text-slate-600">
                <span>Net Subtotal:</span>
                <span className="font-mono font-bold text-slate-900">${subtotalNum.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Commercial Concessions:</span>
                <span className="font-mono font-bold text-emerald-700">-${discountNum.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Estimated Tax:</span>
                <span className="font-mono font-bold text-slate-900">${taxNum.toLocaleString()}</span>
              </div>
              <div className="flex justify-between text-base font-bold text-slate-900 pt-2 border-t border-slate-200">
                <span>Total Payable:</span>
                <span className="font-mono text-emerald-700 text-lg">${totalNum.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Customer Actions */}
        <div className="flex items-center justify-end gap-3 pt-2">
          {activeQuote.status !== 'CONFIRMED' ? (
            <button
              onClick={() => confirmMutation.mutate(activeQuote.id)}
              disabled={confirmMutation.isPending}
              className="flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold text-sm shadow-md transition cursor-pointer"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Accept Terms & Confirm Order</span>
            </button>
          ) : (
            <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-100 text-emerald-800 text-xs font-bold border border-emerald-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Order Officially Confirmed</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
