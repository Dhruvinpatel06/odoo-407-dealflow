import React, { useState } from 'react';
import { 
  CreditCard, 
  Repeat, 
  DollarSign, 
  FileText, 
  Receipt, 
  RotateCcw,
  Loader2
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/StatusBadge';
import { invoiceService, subscriptionService } from '../../services/api';
import { InvoiceResponse } from '../../services/invoiceService';
import { SubscriptionResponse } from '../../services/subscriptionService';

export const BillingView: React.FC = () => {
  const { showNotification } = useApp();
  const queryClient = useQueryClient();

  const [paymentAmount, setPaymentAmount] = useState<number>(0);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<string>('');
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState<boolean>(false);

  // 1. Fetch Invoices
  const { data: invoices = [], isLoading: isInvoicesLoading } = useQuery({
    queryKey: ['invoices'],
    queryFn: () => invoiceService.listInvoices(),
  });

  // 2. Fetch Subscriptions
  const { data: subscriptions = [], isLoading: isSubsLoading } = useQuery({
    queryKey: ['subscriptions'],
    queryFn: () => subscriptionService.listSubscriptions(),
  });

  const invalidateBilling = () => {
    queryClient.invalidateQueries({ queryKey: ['invoices'] });
    queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
  };

  // Payment Mutation
  const paymentMutation = useMutation({
    mutationFn: ({ invoiceId, amount }: { invoiceId: string; amount: number }) =>
      invoiceService.recordPayment(invoiceId, {
        amount,
        payment_method: 'BANK_TRANSFER',
        transaction_reference: `TXN-${Date.now().toString().slice(-6)}`,
      }),
    onSuccess: () => {
      invalidateBilling();
      setIsPaymentModalOpen(false);
      showNotification('Customer payment successfully recorded and reconciled.', 'success');
    },
    onError: (err: any) => {
      showNotification(err?.response?.data?.detail || 'Failed to record payment.', 'error');
    },
  });

  // Modify Subscription Mutation (Prorate)
  const modifySubMutation = useMutation({
    mutationFn: ({ subId, newQty }: { subId: string; newQty: number }) =>
      subscriptionService.applyProration(subId, {
        new_quantity: newQty,
        effective_date: new Date().toISOString(),
      }),
    onSuccess: () => {
      invalidateBilling();
      showNotification('Subscription prorated and updated.', 'success');
    },
    onError: (err: any) => {
      showNotification(err?.response?.data?.detail || 'Proration failed.', 'error');
    },
  });

  const handleRecordPayment = () => {
    if (!selectedInvoiceId || paymentAmount <= 0) return;
    paymentMutation.mutate({ invoiceId: selectedInvoiceId, amount: paymentAmount });
  };

  if (isInvoicesLoading || isSubsLoading) {
    return (
      <div className="p-16 flex flex-col items-center justify-center text-slate-500 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="text-xs font-medium">Loading invoices and recurring subscriptions...</span>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Hybrid Billing & Recurring Subscriptions</h2>
          <p className="text-xs text-slate-500 mt-0.5">Reconcile one-time hardware lines and recurring SaaS subscriptions within identical commercial contracts.</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              const unpaid = invoices.find((i: InvoiceResponse) => Number(i.balance_due || i.amount) > 0);
              if (unpaid) {
                setSelectedInvoiceId(unpaid.id);
                setPaymentAmount(Number(unpaid.balance_due || unpaid.amount));
                setIsPaymentModalOpen(true);
              } else {
                showNotification('All invoices are fully settled.', 'info');
              }
            }}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
          >
            <DollarSign className="w-3.5 h-3.5" />
            <span>Record Customer Payment</span>
          </button>
        </div>
      </div>

      {/* Visual Distinction Banner: Hybrid Billing Architecture */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/40 flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0">
            <Receipt className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-blue-950 uppercase tracking-wide">One-Time Billing Stream</span>
            <p className="text-xs text-blue-900/80 mt-0.5 leading-relaxed">
              Standard commercial invoice generated on fulfillment dispatch. Invoiced once with standard payment terms (e.g. Net 30).
            </p>
          </div>
        </div>

        <div className="p-4 rounded-xl border border-purple-200 bg-purple-50/40 flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-purple-600 text-white flex items-center justify-center shrink-0">
            <Repeat className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-bold text-purple-950 uppercase tracking-wide">Recurring Subscription Stream</span>
            <p className="text-xs text-purple-900/80 mt-0.5 leading-relaxed">
              Automated periodic billing schedule with mid-cycle proration engine and credit-note reconciling.
            </p>
          </div>
        </div>
      </div>

      {/* Section 1: Recurring Subscriptions & Schedules */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Repeat className="w-4 h-4 text-purple-600" />
            <h3 className="text-sm font-bold text-slate-900">Active Recurring Subscriptions ({subscriptions.length})</h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">Automated Proration Active</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[10px]">
                <th className="py-3 px-4">Subscription Service</th>
                <th className="py-3 px-3">Frequency</th>
                <th className="py-3 px-3">Units</th>
                <th className="py-3 px-3">Rate</th>
                <th className="py-3 px-3">Start Date</th>
                <th className="py-3 px-3">Next Billing Date</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-4 text-right">Mid-Cycle Proration</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {subscriptions.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400 text-xs">
                    No recurring subscriptions currently active.
                  </td>
                </tr>
              ) : (
                subscriptions.map((sub: SubscriptionResponse) => {
                  const qtyNum = Number(sub.quantity || 1);
                  const priceNum = Number(sub.unit_price || 0);

                  return (
                    <tr key={sub.id} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900">{sub.product_name || 'Recurring Service'}</div>
                        <div className="text-[10px] text-slate-400 font-mono">Order: {sub.order_id?.substring(0, 8)?.toUpperCase()}</div>
                      </td>
                      <td className="py-3 px-3">
                        <span className="px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 font-bold text-[10px]">
                          {sub.billing_interval || 'MONTHLY'}
                        </span>
                      </td>
                      <td className="py-3 px-3 font-mono font-bold text-slate-800">
                        {qtyNum}
                      </td>
                      <td className="py-3 px-3 font-mono font-bold text-slate-900">
                        ${priceNum.toLocaleString()}
                      </td>
                      <td className="py-3 px-3 font-mono text-slate-600">
                        {sub.start_date ? new Date(sub.start_date).toLocaleDateString() : '-'}
                      </td>
                      <td className="py-3 px-3 font-mono text-slate-800 font-semibold">
                        {sub.next_billing_date ? new Date(sub.next_billing_date).toLocaleDateString() : '-'}
                      </td>
                      <td className="py-3 px-3">
                        <StatusBadge status={sub.status} />
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => modifySubMutation.mutate({ subId: sub.id, newQty: qtyNum + 1 })}
                            disabled={modifySubMutation.isPending}
                            className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-[11px] transition cursor-pointer disabled:opacity-50"
                            title="Add unit with mid-cycle proration"
                          >
                            +1 Unit (Prorate)
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Section 2: Invoices & Payment Reconciliation */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-bold text-slate-900">Commercial Invoices & Credit Notes</h3>
          </div>
          <span className="text-xs text-slate-500">FastAPI Payment Engine Verified</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[10px]">
                <th className="py-3 px-4">Invoice #</th>
                <th className="py-3 px-4">Customer</th>
                <th className="py-3 px-3">Stream Type</th>
                <th className="py-3 px-3">Total Amount</th>
                <th className="py-3 px-3">Paid Amount</th>
                <th className="py-3 px-3">Balance Due</th>
                <th className="py-3 px-3">Due Date</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {invoices.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400 text-xs">
                    No commercial invoices issued yet.
                  </td>
                </tr>
              ) : (
                invoices.map((inv: InvoiceResponse) => {
                  const total = Number(inv.amount || 0);
                  const paid = Number(inv.paid_amount || 0);
                  const balance = inv.balance_due !== undefined ? Number(inv.balance_due) : Math.max(0, total - paid);

                  return (
                    <tr key={inv.id} className="hover:bg-slate-50 transition">
                      <td className="py-3.5 px-4 font-mono font-bold text-blue-600">
                        {inv.invoice_number || inv.id.substring(0, 8)}
                      </td>
                      <td className="py-3.5 px-4 font-semibold text-slate-900">{inv.customer_name || 'Customer'}</td>
                      <td className="py-3.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          inv.invoice_type === 'ONE_TIME' || inv.invoice_type === 'STANDARD'
                            ? 'bg-blue-50 text-blue-700 border border-blue-200' 
                            : 'bg-purple-50 text-purple-700 border border-purple-200'
                        }`}>
                          {inv.invoice_type}
                        </span>
                      </td>
                      <td className="py-3.5 px-3 font-mono font-bold text-slate-900">
                        ${total.toLocaleString()}
                      </td>
                      <td className="py-3.5 px-3 font-mono font-semibold text-emerald-600">
                        ${paid.toLocaleString()}
                      </td>
                      <td className="py-3.5 px-3 font-mono font-semibold text-slate-700">
                        ${balance.toLocaleString()}
                      </td>
                      <td className="py-3.5 px-3 font-mono text-slate-500">
                        {inv.due_date ? new Date(inv.due_date).toLocaleDateString() : '-'}
                      </td>
                      <td className="py-3.5 px-3">
                        <StatusBadge status={inv.status} />
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        {balance > 0 && (
                          <button
                            onClick={() => {
                              setSelectedInvoiceId(inv.id);
                              setPaymentAmount(balance);
                              setIsPaymentModalOpen(true);
                            }}
                            className="px-2.5 py-1 rounded bg-emerald-50 hover:bg-emerald-100 border border-emerald-300 text-emerald-800 font-semibold text-xs transition cursor-pointer"
                          >
                            Pay
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
      </div>

      {/* Record Payment Modal */}
      {isPaymentModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl border border-slate-200 shadow-xl max-w-md w-full p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-emerald-600" />
                <span>Record Customer Payment</span>
              </h3>
              <button
                onClick={() => setIsPaymentModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Target Invoice:</label>
                <select
                  value={selectedInvoiceId}
                  onChange={(e) => {
                    setSelectedInvoiceId(e.target.value);
                    const inv = invoices.find((i: InvoiceResponse) => i.id === e.target.value);
                    if (inv) {
                      const total = Number(inv.amount || 0);
                      const paid = Number(inv.paid_amount || 0);
                      setPaymentAmount(inv.balance_due !== undefined ? Number(inv.balance_due) : Math.max(0, total - paid));
                    }
                  }}
                  className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 font-mono font-medium"
                >
                  {invoices.map((inv: InvoiceResponse) => (
                    <option key={inv.id} value={inv.id}>
                      {inv.invoice_number || inv.id.substring(0, 8)} — {inv.customer_name || 'Customer'}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Payment Amount ($ USD):</label>
                <input
                  type="number"
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(parseFloat(e.target.value) || 0)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 font-mono font-bold text-base text-slate-900"
                />
              </div>

              <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900">
                <span className="font-semibold block">FastAPI Billing Rule:</span>
                Recording payment updates invoice status automatically: Paid Amount = 0 → ISSUED, 0 &lt; Paid &lt; Total → PARTIALLY_PAID, Paid = Total → PAID.
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
              <button
                onClick={() => setIsPaymentModalOpen(false)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={handleRecordPayment}
                disabled={paymentMutation.isPending}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-2xs disabled:opacity-50"
              >
                Confirm Payment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
