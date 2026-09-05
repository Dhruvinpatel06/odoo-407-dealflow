import React, { useState } from 'react';
import { 
  Activity, 
  AlertTriangle, 
  Clock, 
  CheckCircle2, 
  Zap, 
  TrendingDown, 
  ShieldAlert, 
  ArrowRight,
  Filter,
  BellRing,
  ExternalLink
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/StatusBadge';

export const DealHealthView: React.FC = () => {
  const { 
    dealAlerts, 
    acknowledgeAlert, 
    resolveAlert, 
    triggerAlertNudge, 
    setSelectedQuoteId, 
    setCurrentPage,
    quotations 
  } = useApp();

  const [filterType, setFilterType] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');

  const filteredAlerts = dealAlerts.filter(a => {
    const matchesType = filterType === 'ALL' || a.type === filterType;
    const matchesStatus = filterStatus === 'ALL' || a.status === filterStatus;
    return matchesType && matchesStatus;
  });

  const healthyQuotes = quotations.filter(q => q.riskStatus === 'HEALTHY');
  const warningQuotes = quotations.filter(q => q.riskStatus === 'MODERATE');
  const atRiskQuotes = quotations.filter(q => q.riskStatus === 'HIGH_RISK');

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">Deal Health & Anomaly Telemetry</h2>
        <p className="text-xs text-slate-500 mt-0.5">Automated detection of stalled deals, discount divergence anomalies, and delivery promise slippage.</p>
      </div>

      {/* Health Overview Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-white border border-emerald-200 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold text-emerald-700 uppercase tracking-wider">Healthy Pipeline</span>
            <div className="text-2xl font-bold font-mono text-slate-900 mt-1">{healthyQuotes.length} Deals</div>
            <span className="text-xs text-slate-500 mt-0.5 block">Standard velocity & margins</span>
          </div>
          <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-white border border-amber-200 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold text-amber-700 uppercase tracking-wider">Warning Watchlist</span>
            <div className="text-2xl font-bold font-mono text-slate-900 mt-1">{warningQuotes.length} Deals</div>
            <span className="text-xs text-slate-500 mt-0.5 block">Near discount thresholds</span>
          </div>
          <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-white border border-rose-200 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold text-rose-700 uppercase tracking-wider">High Risk Critical</span>
            <div className="text-2xl font-bold font-mono text-slate-900 mt-1">{atRiskQuotes.length} Deals</div>
            <span className="text-xs text-slate-500 mt-0.5 block">Breached governance / stalled</span>
          </div>
          <div className="w-10 h-10 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center font-bold">
            <ShieldAlert className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 font-semibold text-slate-700">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span>Filter Signals:</span>
          </div>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium"
          >
            <option value="ALL">All Signal Types</option>
            <option value="DISCOUNT_ANOMALY">Discount Anomalies</option>
            <option value="STALLED">Stalled Quotations</option>
            <option value="DELIVERY_SLIPPAGE">Delivery Slippage</option>
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 font-medium"
          >
            <option value="ALL">All Alert Statuses</option>
            <option value="OPEN">Open Only</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="RESOLVED">Resolved</option>
          </select>
        </div>

        <span className="text-slate-500">
          Showing <strong className="text-slate-800">{filteredAlerts.length}</strong> active deal signals
        </span>
      </div>

      {/* Actionable Alerts Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[10px]">
                <th className="py-3 px-4">Severity & Signal</th>
                <th className="py-3 px-4">Quote & Customer</th>
                <th className="py-3 px-4">Root Cause Reason</th>
                <th className="py-3 px-3">Owner</th>
                <th className="py-3 px-3">Age</th>
                <th className="py-3 px-3">Alert Status</th>
                <th className="py-3 px-4 text-right">Operational Nudge</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredAlerts.map((alt) => {
                const isHigh = alt.severity === 'HIGH';
                return (
                  <tr key={alt.id} className="hover:bg-slate-50 transition">
                    {/* Severity & Type */}
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${isHigh ? 'bg-rose-500' : 'bg-amber-500'}`} />
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          isHigh ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-amber-50 text-amber-700 border border-amber-200'
                        }`}>
                          {alt.type.replace('_', ' ')}
                        </span>
                      </div>
                    </td>

                    {/* Quote & Customer */}
                    <td className="py-3.5 px-4">
                      <button
                        onClick={() => {
                          setSelectedQuoteId(alt.quotationId);
                          setCurrentPage('quote-builder');
                        }}
                        className="font-mono font-bold text-blue-600 hover:underline block text-left"
                      >
                        {alt.quoteNumber}
                      </button>
                      <span className="font-semibold text-slate-900">{alt.customerName}</span>
                    </td>

                    {/* Root Cause Reason */}
                    <td className="py-3.5 px-4 max-w-sm">
                      <p className="text-slate-700 leading-snug">{alt.reason}</p>
                      <div className="text-[10px] text-blue-600 mt-1 font-medium">
                        Recommendation: {alt.suggestedAction}
                      </div>
                    </td>

                    {/* Owner */}
                    <td className="py-3.5 px-3 text-slate-700 font-medium">
                      {alt.ownerName}
                    </td>

                    {/* Age */}
                    <td className="py-3.5 px-3 font-mono text-slate-500">
                      {alt.ageDays} days
                    </td>

                    {/* Status */}
                    <td className="py-3.5 px-3">
                      <StatusBadge status={alt.status} />
                    </td>

                    {/* Actions */}
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {alt.status === 'OPEN' && (
                          <>
                            <button
                              onClick={() => triggerAlertNudge(alt.id)}
                              className="px-2.5 py-1 rounded bg-blue-50 hover:bg-blue-100 border border-blue-200 text-blue-700 font-semibold text-[11px] transition flex items-center gap-1 cursor-pointer"
                              title="Send automated nudge to rep"
                            >
                              <BellRing className="w-3 h-3" />
                              <span>Nudge Rep</span>
                            </button>
                            <button
                              onClick={() => acknowledgeAlert(alt.id)}
                              className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 font-medium text-[11px] transition cursor-pointer"
                            >
                              Ack
                            </button>
                          </>
                        )}
                        {alt.status === 'ACKNOWLEDGED' && (
                          <button
                            onClick={() => resolveAlert(alt.id)}
                            className="px-2.5 py-1 rounded bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-700 font-semibold text-[11px] transition cursor-pointer"
                          >
                            Resolve
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
