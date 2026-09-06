import React from 'react';
import { 
  TrendingUp, 
  CheckCircle2, 
  AlertTriangle, 
  DollarSign, 
  ArrowRight, 
  Plus, 
  Sparkles, 
  Building2, 
  Check, 
  RotateCcw, 
  CreditCard, 
  Percent,
  Clock
} from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/StatusBadge';
import { RiskBadge } from '../common/RiskBadge';
import { getRoleMeta } from '../../utils/rbac';
import { 
  useQuotationsQuery, 
  useApprovalsQuery, 
  useCustomersQuery 
} from '../../hooks/useBackendData';
import { quotationService, approvalService } from '../../services/api';
import { QuotationResponse } from '../../services/quotationService';
import { ApprovalInstanceResponse } from '../../services/approvalService';

export const DashboardView: React.FC = () => {
  const { 
    currentUser, 
    setCurrentPage, 
    setSelectedQuoteId, 
    showNotification 
  } = useApp();

  const queryClient = useQueryClient();
  const role = currentUser.role;
  const roleMeta = getRoleMeta(role);

  // Queries
  const { data: quotations = [] } = useQuotationsQuery();
  const { data: approvals = [] } = useApprovalsQuery();
  const { data: customers = [] } = useCustomersQuery();

  // Metrics
  const totalPipeline = quotations.reduce((acc: number, q: QuotationResponse) => acc + Number(q.total_amount || 0), 0);
  const pendingApprovals = approvals.filter((a: ApprovalInstanceResponse) => a.status === 'PENDING');
  const highRiskQuotes = quotations.filter((q: QuotationResponse) => q.risk_status === 'HIGH_RISK' || Number(q.risk_score || 0) >= 60);
  const avgMargin = quotations.length > 0 
    ? quotations.reduce((acc: number, q: QuotationResponse) => acc + Number(q.margin_percent || 0), 0) / quotations.length 
    : 35.0;

  const repQuotes = quotations.filter((q: QuotationResponse) => 
    q.sales_rep_name === currentUser.name || q.sales_rep_id === currentUser.id
  );
  const repPipeline = (repQuotes.length > 0 ? repQuotes : quotations).reduce(
    (acc: number, q: QuotationResponse) => acc + Number(q.total_amount || 0), 0
  );
  const repQuota = 135000;
  const repAttainment = Math.min(100, Math.round((repPipeline / repQuota) * 100));

  const handleCreateQuote = async () => {
    try {
      const defaultCust = customers[0];
      if (!defaultCust) {
        showNotification('No customers available to create quotation.', 'warning');
        return;
      }
      const newQuote = await quotationService.createQuotation({ customer_id: defaultCust.id });
      queryClient.invalidateQueries({ queryKey: ['quotations'] });
      queryClient.invalidateQueries({ queryKey: ['pipeline'] });
      setSelectedQuoteId(newQuote.id);
      setCurrentPage('quote-builder');
      showNotification('New quotation draft initialized.', 'success');
    } catch (err: any) {
      showNotification(err?.response?.data?.detail || 'Failed to create quotation.', 'error');
    }
  };

  const handleQuickApprove = async (appId: string, quoteNum?: string) => {
    try {
      await approvalService.approve(appId, { comment: 'Approved directly via Sales Manager Priority Dashboard.' });
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      queryClient.invalidateQueries({ queryKey: ['quotations'] });
      showNotification(`Approved ${quoteNum || 'quotation'} as Sales Manager.`, 'success');
    } catch (err: any) {
      showNotification(err?.response?.data?.detail || 'Approval failed.', 'error');
    }
  };

  const handleQuickRevision = async (appId: string, quoteNum?: string) => {
    try {
      await approvalService.returnForRevision(appId, { comment: 'Returned from Manager Dashboard for revision.' });
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      queryClient.invalidateQueries({ queryKey: ['quotations'] });
      showNotification(`Returned ${quoteNum || 'quotation'} for revision.`, 'warning');
    } catch (err: any) {
      showNotification(err?.response?.data?.detail || 'Return failed.', 'error');
    }
  };

  return (
    <div className="p-8 space-y-6 flex-1 max-w-7xl mx-auto">
      {/* Role-Specific Header Banner */}
      <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold text-[#111827] tracking-tight">
              {role === 'SALES_REP' && 'Sales Representative Workspace'}
              {role === 'SALES_MANAGER' && 'Sales Management & Team Governance Hub'}
              {role === 'FINANCE_OPERATIONS' && 'Revenue Operations & Financial Governance'}
              {role === 'ADMIN' && 'Platform Administration & System Governance'}
            </h1>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${roleMeta.badgeColor}`}>
              {roleMeta.label}
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {role === 'SALES_REP' && `Welcome back, ${currentUser.name}. Track your personal quota attainment, manage active client deals, and monitor approval routing.`}
            {role === 'SALES_MANAGER' && `Welcome back, ${currentUser.name}. Oversee team pipeline velocity, review pending discount requests, and protect gross margin thresholds.`}
            {role === 'FINANCE_OPERATIONS' && `Welcome back, ${currentUser.name}. Monitor cash collection, COGS margin floors, recurring subscription ARR, and Tier-2 risk approvals.`}
            {role === 'ADMIN' && `Welcome back, ${currentUser.name}. Manage enterprise RBAC matrices, authoritative discount rules, warehouse allocations, and immutable audit trails.`}
          </p>
        </div>

        {/* Primary Role Action */}
        <div className="flex items-center gap-2">
          {role === 'SALES_REP' && (
            <button
              onClick={handleCreateQuote}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Create Quotation</span>
            </button>
          )}

          {role === 'SALES_MANAGER' && (
            <button
              onClick={() => setCurrentPage('approvals')}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Open Approval Center ({pendingApprovals.length})</span>
            </button>
          )}

          {role === 'FINANCE_OPERATIONS' && (
            <button
              onClick={() => setCurrentPage('billing')}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
            >
              <CreditCard className="w-4 h-4" />
              <span>View Hybrid Invoicing</span>
            </button>
          )}

          {role === 'ADMIN' && (
            <button
              onClick={() => setCurrentPage('discount-ceilings')}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
            >
              <Percent className="w-4 h-4" />
              <span>Configure Policy Ceilings</span>
            </button>
          )}
        </div>
      </div>

      {/* PROMINENT SECTION FOR SALES MANAGERS: Pending Approvals Priority Banner */}
      {role === 'SALES_MANAGER' && pendingApprovals.length > 0 && (
        <div className="bg-gradient-to-r from-purple-50/90 via-white to-blue-50/50 rounded-xl border border-purple-200 p-5 shadow-xs">
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-purple-100">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-purple-600 text-white flex items-center justify-center font-bold shadow-xs">
                <CheckCircle2 className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-gray-900">
                  Priority Approvals Requiring Your Sign-Off ({pendingApprovals.length})
                </h3>
                <p className="text-[11px] text-gray-500">
                  Authoritative Level 1 Manager Governance: Deals exceeding rep discretion ceilings.
                </p>
              </div>
            </div>
            <button
              onClick={() => setCurrentPage('approvals')}
              className="text-xs font-bold text-purple-700 hover:underline cursor-pointer"
            >
              View Full Approval Queue &rarr;
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {pendingApprovals.slice(0, 2).map((app: ApprovalInstanceResponse) => (
              <div key={app.id} className="bg-white rounded-lg border border-purple-100 p-4 shadow-2xs space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-mono font-bold text-[#2563EB] text-xs">{app.quotation_number || 'Quote'}</span>
                    <span className="font-bold text-gray-900 text-xs ml-2">{app.customer_name || 'Customer'}</span>
                  </div>
                  <RiskBadge score={Number(app.risk_score || 0)} />
                </div>

                <div className="text-xs text-gray-600">
                  Submitted by: <strong className="text-gray-900">{app.sales_rep_name || 'Sales Rep'}</strong> &bull; Amount:{' '}
                  <strong className="font-mono text-gray-900">${Number(app.total_amount || 0).toLocaleString()}</strong>
                </div>

                {(app.reasons || []).length > 0 && (
                  <p className="text-[11px] text-gray-500 bg-gray-50 p-2 rounded border border-gray-100">
                    Reason: {app.reasons![0]}
                  </p>
                )}

                <div className="flex items-center justify-between pt-1">
                  <button
                    onClick={() => {
                      setSelectedQuoteId(app.quotation_id);
                      setCurrentPage('quote-builder');
                    }}
                    className="text-[11px] font-semibold text-gray-600 hover:text-gray-900 cursor-pointer"
                  >
                    Inspect Deal Details
                  </button>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleQuickRevision(app.id, app.quotation_number)}
                      className="flex items-center gap-1 px-2.5 py-1 rounded border border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-800 text-[11px] font-semibold transition cursor-pointer"
                    >
                      <RotateCcw className="w-3 h-3 text-amber-600" />
                      <span>Request Revision</span>
                    </button>
                    <button
                      onClick={() => handleQuickApprove(app.id, app.quotation_number)}
                      className="flex items-center gap-1 px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-bold shadow-2xs transition cursor-pointer"
                    >
                      <Check className="w-3 h-3" />
                      <span>Approve (L1)</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Role-Specific 4-Column KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Card 1 */}
        <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-xs">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
            {role === 'SALES_REP' ? 'My Active Pipeline' : role === 'SALES_MANAGER' ? 'Team Pipeline' : role === 'FINANCE_OPERATIONS' ? 'Invoiced ARR' : 'System Volume'}
          </p>
          <p className="text-2xl font-bold mt-1 text-[#111827]">
            ${Math.round(role === 'SALES_REP' ? repPipeline : totalPipeline).toLocaleString()}
          </p>
          <div className="mt-2 flex items-center gap-1 text-xs text-green-600 font-medium">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>{quotations.length} Tracked Deal(s)</span>
          </div>
        </div>

        {/* Card 2 */}
        <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-xs">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
            {role === 'SALES_REP' ? 'Target Attainment' : role === 'SALES_MANAGER' ? 'Team Avg. Margin' : role === 'FINANCE_OPERATIONS' ? 'COGS Floor Adherence' : 'Active RBAC Roles'}
          </p>
          <p className="text-2xl font-bold mt-1 text-[#111827]">
            {role === 'SALES_REP' ? `${repAttainment}%` : role === 'ADMIN' ? '5 Roles' : `${avgMargin.toFixed(1)}%`}
          </p>
          <div className="mt-2 flex items-center gap-1 text-xs text-blue-600 font-medium">
            <span>
              {role === 'SALES_REP' ? `$${(repQuota / 1000).toFixed(0)}k Q3 Quota Target` : role === 'ADMIN' ? 'Full RBAC Policy Enforced' : 'Within Corporate Margin Floor'}
            </span>
          </div>
        </div>

        {/* Card 3 */}
        <div 
          onClick={() => setCurrentPage('approvals')}
          className="bg-white p-5 rounded-xl border border-gray-100 shadow-xs cursor-pointer hover:border-gray-200 transition"
        >
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
            Pending Sign-Offs
          </p>
          <p className="text-2xl font-bold mt-1 text-purple-700">
            {pendingApprovals.length}
          </p>
          <div className="mt-2 flex items-center gap-2">
            <span className="px-2 py-0.5 text-[10px] rounded-full font-bold uppercase bg-purple-100 text-purple-800">
              {pendingApprovals.length > 0 ? 'Action Required' : 'All Clear'}
            </span>
          </div>
        </div>

        {/* Card 4 */}
        <div 
          onClick={() => setCurrentPage('quotations')}
          className="bg-white p-5 rounded-xl border border-gray-100 shadow-xs border-l-4 border-l-red-500 cursor-pointer hover:border-gray-200 transition"
        >
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
            High Risk Deals
          </p>
          <p className="text-2xl font-bold mt-1 text-red-600">
            {String(highRiskQuotes.length).padStart(2, '0')}
          </p>
          <p className="text-[10px] text-gray-400 mt-2">
            {highRiskQuotes.length > 0 ? `Requires policy ceiling review` : 'All deals within policy tolerance'}
          </p>
        </div>
      </div>

      {/* Main Content Grid: 2 Cols Table, 1 Col DealFlow Intelligence */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Quotations Table */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-100 shadow-xs overflow-hidden flex flex-col">
          <div className="p-5 border-b border-gray-100 flex justify-between items-center">
            <div>
              <h3 className="font-bold text-gray-800">
                {role === 'SALES_REP' ? 'My Quotations & Accounts' : 'Commercial Quotations & Pipeline'}
              </h3>
              <p className="text-[11px] text-gray-400">
                Authoritative commercial governance view
              </p>
            </div>
            <button 
              onClick={() => setCurrentPage('quotations')}
              className="text-xs font-semibold text-[#2563EB] hover:underline cursor-pointer"
            >
              View All Deals &rarr;
            </button>
          </div>

          <div className="flex-1 overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-gray-50 text-[11px] uppercase tracking-wider text-gray-500">
                  <th className="px-5 py-3 font-semibold">ID</th>
                  <th className="px-5 py-3 font-semibold">Customer</th>
                  {role !== 'SALES_REP' && <th className="px-5 py-3 font-semibold">Rep</th>}
                  <th className="px-5 py-3 font-semibold">Amount</th>
                  <th className="px-5 py-3 font-semibold text-center">Margin</th>
                  <th className="px-5 py-3 font-semibold text-center">Risk</th>
                  <th className="px-5 py-3 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody className="text-sm divide-y divide-gray-100">
                {quotations.slice(0, 5).map((q: QuotationResponse) => {
                  const marginNum = Number(q.margin_percent || 0);
                  const totalNum = Number(q.total_amount || 0);
                  const riskNum = Number(q.risk_score || 0);

                  return (
                    <tr 
                      key={q.id}
                      onClick={() => {
                        setSelectedQuoteId(q.id);
                        setCurrentPage('quote-builder');
                      }}
                      className="hover:bg-gray-50 transition-colors cursor-pointer"
                    >
                      <td className="px-5 py-4 font-mono text-xs text-gray-400">{q.quotation_number}</td>
                      <td className="px-5 py-4 font-bold text-gray-900">
                        <div>{q.customer_name || 'Account'}</div>
                        {q.customer_tier_name && (
                          <div className="text-[10px] text-gray-400 font-normal">Tier: {q.customer_tier_name}</div>
                        )}
                      </td>
                      {role !== 'SALES_REP' && (
                        <td className="px-5 py-4 text-xs text-gray-600">{q.sales_rep_name || 'Sales Rep'}</td>
                      )}
                      <td className="px-5 py-4 font-mono text-gray-800 font-medium">
                        ${totalNum.toLocaleString()}
                      </td>
                      <td className={`px-5 py-4 text-center font-mono font-medium ${
                        marginNum < 20 ? 'text-red-500 font-bold' : 'text-gray-600'
                      }`}>
                        {marginNum.toFixed(1)}%
                      </td>
                      <td className="px-5 py-4 text-center">
                        <RiskBadge score={riskNum} status={q.risk_status} />
                      </td>
                      <td className="px-5 py-4">
                        <StatusBadge status={q.status} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: DealFlow Intelligence */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-xs p-5 flex flex-col">
          <div className="flex items-center justify-between pb-3.5 border-b border-gray-100 mb-4">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-blue-50 text-[#2563EB] flex items-center justify-center shrink-0 border border-blue-100">
                <Sparkles className="w-3.5 h-3.5" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-gray-900 tracking-tight">DealFlow Intelligence</h3>
                <p className="text-[11px] text-gray-500">
                  Governance insights for your pipeline
                </p>
              </div>
            </div>
            <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-gray-100 text-gray-600 border border-gray-200">
              Policy Engine
            </span>
          </div>

          <div className="flex-1 space-y-4">
            {highRiskQuotes.length > 0 ? (
              <div className="bg-rose-50/50 p-4 rounded-xl border border-rose-200/80 space-y-2.5">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                    <span className="text-xs font-bold text-rose-950 uppercase tracking-wide">
                      Governance Breaches
                    </span>
                  </div>
                  <span className="px-2 py-0.5 bg-rose-100 text-rose-700 border border-rose-200 text-[10px] font-bold rounded-full uppercase">
                    Requires Review
                  </span>
                </div>

                <p className="text-xs text-rose-950/90 leading-relaxed font-normal">
                  {highRiskQuotes[0].quotation_number} ({highRiskQuotes[0].customer_name}) discounts exceed policy ceilings.
                </p>
              </div>
            ) : (
              <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/40 text-emerald-900 text-xs">
                <span className="font-bold block mb-1">Portfolio Health: Optimal</span>
                All active quotations comply with corporate gross margin floors and customer tier discount allowances.
              </div>
            )}

            {/* Quota Velocity */}
            <div className="p-4 rounded-xl border border-gray-100 bg-gray-50/60 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Attainment Velocity
                </span>
                <span className="text-xs font-bold font-mono text-[#2563EB]">
                  {repAttainment}%
                </span>
              </div>

              <div className="w-full h-2 bg-gray-200/80 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-[#2563EB] rounded-full transition-all duration-300"
                  style={{ width: `${repAttainment}%` }}
                />
              </div>

              <div className="flex justify-between items-center text-[11px] text-gray-500">
                <span>Current Pipeline Volume</span>
                <span className="font-medium text-gray-600">
                  ${Math.round(totalPipeline).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
