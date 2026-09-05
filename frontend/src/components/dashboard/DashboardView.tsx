import React from 'react';
import { 
  TrendingUp, 
  FileText, 
  CheckCircle2, 
  AlertTriangle, 
  Activity, 
  DollarSign, 
  ArrowRight, 
  Plus, 
  ShieldAlert,
  Clock,
  Sparkles,
  Building2,
  ChevronRight,
  UserCheck,
  Shield,
  Layers,
  Settings,
  Check,
  RotateCcw,
  Target,
  BarChart3,
  CreditCard
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/StatusBadge';
import { RiskBadge } from '../common/RiskBadge';
import { getRoleMeta } from '../../utils/rbac';

export const DashboardView: React.FC = () => {
  const { 
    quotations, 
    approvals, 
    dealAlerts, 
    setCurrentPage, 
    setSelectedQuoteId, 
    auditLogs,
    currentUser,
    approveCurrentStep,
    returnForRevision,
    showNotification
  } = useApp();

  const role = currentUser.role;
  const roleMeta = getRoleMeta(role);

  // Common calculations
  const totalPipeline = quotations.reduce((acc, q) => acc + q.totalAmount, 0);
  const pendingApprovals = approvals.filter(a => a.status === 'PENDING');
  const highRiskQuotes = quotations.filter(q => q.riskStatus === 'HIGH_RISK');
  const avgMargin = quotations.reduce((acc, q) => acc + q.blendedMarginPercent, 0) / (quotations.length || 1);

  // Rep-specific calculations
  const repQuotes = quotations.filter(q => q.salesRepName === currentUser.name || q.salesRepName === 'Sarah Chen');
  const repPipeline = repQuotes.reduce((acc, q) => acc + q.totalAmount, 0);
  const repQuota = 135000;
  const repAttainment = Math.round((repPipeline / repQuota) * 100);
  const repPendingApprovals = approvals.filter(a => 
    a.status === 'PENDING' && (a.salesRepName === currentUser.name || a.salesRepName === 'Sarah Chen')
  );

  // Manager-specific calculations
  const managerPending = approvals.filter(a => 
    a.status === 'PENDING' && a.currentStepRole === 'SALES_MANAGER'
  );
  const discountBreachQuotes = quotations.filter(q => 
    q.lines.some(l => l.discountExcessPercent > 0)
  );

  // Handle fast approval right from Manager Dashboard
  const handleQuickApprove = (appId: string, quoteNum: string) => {
    approveCurrentStep(appId, 'Approved directly via Sales Manager Priority Dashboard.');
    showNotification(`Approved ${quoteNum} as Sales Manager. Status updated in governance ledger.`, 'success');
  };

  const handleQuickRevision = (appId: string, quoteNum: string) => {
    returnForRevision(appId, 'Returned from Manager Dashboard. Please add recurring service support.');
    showNotification(`Returned ${quoteNum} for revision. Sales Rep notified.`, 'warning');
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
            {role === 'SALES_REP' && `Welcome back, ${currentUser.name}. Track your personal quota attainment, manage active client negotiations, and monitor approval routing.`}
            {role === 'SALES_MANAGER' && `Welcome back, ${currentUser.name}. Oversee team pipeline velocity, review pending discount requests, and protect gross margin thresholds.`}
            {role === 'FINANCE_OPERATIONS' && `Welcome back, ${currentUser.name}. Monitor cash collection, COGS margin floors, recurring subscription ARR, and Tier-2 risk approvals.`}
            {role === 'ADMIN' && `Welcome back, ${currentUser.name}. Manage enterprise RBAC matrices, authoritative discount rules, warehouse allocations, and immutable audit trails.`}
          </p>
        </div>

        {/* Primary Role Action */}
        <div className="flex items-center gap-2">
          {role === 'SALES_REP' && (
            <button
              onClick={() => {
                setSelectedQuoteId('q-1048');
                setCurrentPage('quote-builder');
              }}
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
              onClick={() => setCurrentPage('admin')}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
            >
              <Settings className="w-4 h-4" />
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

          {/* Quick-action items list */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {pendingApprovals.slice(0, 2).map((app) => (
              <div key={app.id} className="bg-white rounded-lg border border-purple-100 p-4 shadow-2xs space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-mono font-bold text-[#2563EB] text-xs">{app.quoteNumber}</span>
                    <span className="font-bold text-gray-900 text-xs ml-2">{app.customerName}</span>
                  </div>
                  <RiskBadge score={app.riskScore} />
                </div>

                <div className="text-xs text-gray-600">
                  Submitted by: <strong className="text-gray-900">{app.salesRepName}</strong> &bull; Amount:{' '}
                  <strong className="font-mono text-gray-900">${app.amount.toLocaleString()}</strong>
                </div>

                <p className="text-[11px] text-gray-500 bg-gray-50 p-2 rounded border border-gray-100">
                  Reason: {app.reason}
                </p>

                {/* Manager Quick Action Controls */}
                <div className="flex items-center justify-between pt-1">
                  <button
                    onClick={() => {
                      setSelectedQuoteId(app.quotationId);
                      setCurrentPage('quote-builder');
                    }}
                    className="text-[11px] font-semibold text-gray-600 hover:text-gray-900 cursor-pointer"
                  >
                    Inspect Deal Details
                  </button>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleQuickRevision(app.id, app.quoteNumber)}
                      className="flex items-center gap-1 px-2.5 py-1 rounded border border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-800 text-[11px] font-semibold transition cursor-pointer"
                    >
                      <RotateCcw className="w-3 h-3 text-amber-600" />
                      <span>Request Revision</span>
                    </button>
                    <button
                      onClick={() => handleQuickApprove(app.id, app.quoteNumber)}
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
        <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
            {role === 'SALES_REP' ? 'My Active Pipeline' : role === 'SALES_MANAGER' ? 'Team Pipeline' : role === 'FINANCE_OPERATIONS' ? 'Invoiced ARR' : 'System Volume'}
          </p>
          <p className="text-2xl font-bold mt-1 text-[#111827]">
            {role === 'SALES_REP' ? `$${Math.round(repPipeline).toLocaleString()}` : `$${Math.round(totalPipeline).toLocaleString()}`}
          </p>
          <div className="mt-2 flex items-center gap-1 text-xs text-green-600 font-medium">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>{role === 'SALES_REP' ? '3 Qualified Deals' : '+12.4% vs last month'}</span>
          </div>
        </div>

        {/* Card 2 */}
        <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
            {role === 'SALES_REP' ? 'Target Attainment' : role === 'SALES_MANAGER' ? 'Team Avg. Margin' : role === 'FINANCE_OPERATIONS' ? 'COGS Floor Adherence' : 'Active RBAC Roles'}
          </p>
          <p className="text-2xl font-bold mt-1 text-[#111827]">
            {role === 'SALES_REP' ? `${repAttainment}%` : role === 'ADMIN' ? '5 Roles' : `${avgMargin.toFixed(1)}%`}
          </p>
          <div className="mt-2 flex items-center gap-1 text-xs text-blue-600 font-medium">
            <span>
              {role === 'SALES_REP' ? `$${(repQuota / 1000).toFixed(0)}k Q3 Quota Target` : role === 'ADMIN' ? 'Full RBAC Policy Enforced' : 'Within 30% Floor Limit'}
            </span>
          </div>
        </div>

        {/* Card 3 */}
        <div 
          onClick={() => setCurrentPage('approvals')}
          className={`bg-white p-5 rounded-xl border shadow-sm cursor-pointer transition ${
            role === 'SALES_MANAGER' ? 'border-purple-200 bg-purple-50/20 hover:border-purple-300' : 'border-gray-100 hover:border-gray-200'
          }`}
        >
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
            {role === 'SALES_REP' ? 'My Submitted Approvals' : role === 'SALES_MANAGER' ? 'Pending Sign-Offs' : role === 'FINANCE_OPERATIONS' ? 'Tier 2 Finance Sign-Offs' : 'Audit Logs Today'}
          </p>
          <p className={`text-2xl font-bold mt-1 ${role === 'SALES_MANAGER' ? 'text-purple-700' : 'text-[#111827]'}`}>
            {role === 'SALES_REP' ? repPendingApprovals.length : role === 'ADMIN' ? auditLogs.length : pendingApprovals.length}
          </p>
          <div className="mt-2 flex items-center gap-2">
            <span className={`px-2 py-0.5 text-[10px] rounded-full font-bold uppercase ${
              role === 'SALES_MANAGER' ? 'bg-purple-100 text-purple-800' : 'bg-blue-50 text-blue-700'
            }`}>
              {role === 'SALES_REP' ? 'Tracking Mode' : role === 'SALES_MANAGER' ? 'Action Required' : 'Monitored'}
            </span>
          </div>
        </div>

        {/* Card 4 */}
        <div 
          onClick={() => setCurrentPage(role === 'FINANCE_OPERATIONS' ? 'billing' : 'deal-health')}
          className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm border-l-4 border-l-red-500 cursor-pointer hover:border-gray-200 transition"
        >
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
            {role === 'FINANCE_OPERATIONS' ? 'Unbilled Backlog' : role === 'SALES_REP' ? 'Ceiling Warnings' : 'High Risk Deals'}
          </p>
          <p className="text-2xl font-bold mt-1 text-red-600">
            {role === 'FINANCE_OPERATIONS' ? '$84,200' : role === 'SALES_REP' ? '1 Quote' : String(highRiskQuotes.length).padStart(2, '0')}
          </p>
          <p className="text-[10px] text-gray-400 mt-2">
            {highRiskQuotes.length > 0 ? `Action required for ${highRiskQuotes[0].customerName}` : 'All deals within tolerance'}
          </p>
        </div>
      </div>

      {/* Main Content Grid: 2 Cols Table, 1 Col DealFlow Intelligence */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols): Table of Quotations tailored to Role */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden flex flex-col">
          <div className="p-5 border-b border-gray-100 flex justify-between items-center">
            <div>
              <h3 className="font-bold text-gray-800">
                {role === 'SALES_REP' ? 'My Quotations & Accounts' : role === 'SALES_MANAGER' ? 'Team Quotations & Exception Radar' : 'Commercial Quotations'}
              </h3>
              <p className="text-[11px] text-gray-400">
                {role === 'SALES_REP' ? 'Filtered to your assigned accounts' : 'Authoritative commercial governance view'}
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
                {(role === 'SALES_REP' ? repQuotes : quotations).slice(0, 5).map((q) => (
                  <tr 
                    key={q.id}
                    onClick={() => {
                      setSelectedQuoteId(q.id);
                      setCurrentPage('quote-builder');
                    }}
                    className="hover:bg-gray-50 transition-colors cursor-pointer"
                  >
                    <td className="px-5 py-4 font-mono text-xs text-gray-400">{q.quoteNumber}</td>
                    <td className="px-5 py-4 font-bold text-gray-900">
                      <div>{q.customerName}</div>
                      <div className="text-[10px] text-gray-400 font-normal">Tier: {q.customerTier}</div>
                    </td>
                    {role !== 'SALES_REP' && (
                      <td className="px-5 py-4 text-xs text-gray-600">{q.salesRepName}</td>
                    )}
                    <td className="px-5 py-4 font-mono text-gray-800 font-medium">
                      ${q.totalAmount.toLocaleString()}
                    </td>
                    <td className={`px-5 py-4 text-center font-mono font-medium ${
                      q.blendedMarginPercent < 20 ? 'text-red-500 font-bold' : 'text-gray-600'
                    }`}>
                      {q.blendedMarginPercent}%
                    </td>
                    <td className="px-5 py-4 text-center">
                      <RiskBadge score={q.blendedRiskScore} status={q.riskStatus} />
                    </td>
                    <td className="px-5 py-4">
                      <StatusBadge status={q.stage} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column (1 Col): Signature Dark DealFlow Intelligence Card tailored to Role */}
        <div className="bg-[#111827] text-white rounded-xl shadow-xl p-6 flex flex-col border border-slate-800">
          <div className="flex items-center gap-2 mb-6">
            <div className="p-1.5 bg-blue-600 rounded-md">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-sm tracking-wide uppercase text-white">DealFlow Intelligence</h3>
              <span className="text-[10px] text-slate-400 font-mono">
                {role === 'SALES_REP' && 'Representative Guidance'}
                {role === 'SALES_MANAGER' && 'Governance Radar'}
                {role === 'FINANCE_OPERATIONS' && 'Financial Risk Guard'}
                {role === 'ADMIN' && 'Policy Engine Health'}
              </span>
            </div>
          </div>

          <div className="flex-1 space-y-5">
            {/* Intelligence Alert */}
            <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700">
              <div className="flex justify-between items-start mb-2">
                <p className="text-xs font-bold text-slate-400 uppercase">
                  {role === 'SALES_REP' ? 'Submission Alert' : 'Governance Alert'}
                </p>
                <span className="px-1.5 py-0.5 bg-red-500 text-[10px] font-bold rounded text-white">HIGH RISK</span>
              </div>
              <p className="text-sm leading-snug text-slate-200">
                {role === 'SALES_REP' 
                  ? 'NovaTech (QT-9405) discount exceeds Gold tier limit by 8.5%. Awaiting Marcus Vance.'
                  : 'Novatech (QT-9405) discount exceeds tier ceiling by 8.5%.'}
              </p>
              <div className="mt-3 p-2 bg-slate-900 rounded border border-slate-700 text-[11px] text-slate-300 italic">
                {role === 'SALES_REP' 
                  ? '"Tip: Adding a bundled support contract can reduce risk score below approval trigger."' 
                  : '"Margin impact reduces net profit below corporate target. Level 1 approval required."'}
              </div>
            </div>

            {/* Smart Recommendation */}
            <div className="p-4 border border-blue-500/30 bg-blue-500/5 rounded-lg">
              <p className="text-xs font-bold text-blue-400 uppercase mb-2">Smart Upsell Strategy</p>
              <p className="text-sm text-slate-200">
                Add <span className="font-bold text-white">Premium Support Bundle</span> to NovaTech to offset margin loss.
              </p>
              <div className="mt-3 flex justify-between items-center">
                <span className="text-xs font-bold text-green-400">+4.2% Margin Lift</span>
                <button 
                  onClick={() => {
                    setSelectedQuoteId('q-1049');
                    setCurrentPage('quote-builder');
                  }}
                  className="text-[11px] bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded transition-colors text-white font-medium cursor-pointer"
                >
                  Add to Quote
                </button>
              </div>
            </div>

            {/* Health Meter */}
            <div className="pt-4 border-t border-slate-800">
              <p className="text-[10px] uppercase font-bold text-slate-500 tracking-widest mb-3">
                {role === 'SALES_REP' ? 'Quota Velocity' : 'Team Governance Index'}
              </p>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div 
                  className={`h-full ${role === 'SALES_REP' ? 'bg-emerald-500 w-[92%]' : 'bg-blue-500 w-[72%]'}`}
                ></div>
              </div>
              <div className="flex justify-between mt-2 text-[11px] font-medium">
                <span className="text-slate-400">
                  {role === 'SALES_REP' ? 'Target Attainment' : 'Operational Efficiency'}
                </span>
                <span className="text-blue-400">
                  {role === 'SALES_REP' ? '92%' : '72%'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Secondary Operational Row: Pending Approvals & Immutable Audit Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Approvals Overview */}
        <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-gray-100 mb-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#2563EB]" />
              <h3 className="text-sm font-bold text-gray-800">
                {role === 'SALES_REP' ? 'My Active Approval Submissions' : `Pending Approvals Queue (${pendingApprovals.length})`}
              </h3>
            </div>
            <button
              onClick={() => setCurrentPage('approvals')}
              className="text-xs text-[#2563EB] font-semibold hover:underline cursor-pointer"
            >
              {role === 'SALES_REP' ? 'Track Status' : 'Review All'}
            </button>
          </div>

          <div className="space-y-3">
            {pendingApprovals.map((app) => (
              <div
                key={app.id}
                onClick={() => setCurrentPage('approvals')}
                className={`p-3.5 rounded-lg border transition cursor-pointer ${
                  role === 'SALES_MANAGER' 
                    ? 'border-purple-200 bg-purple-50/40 hover:bg-purple-50' 
                    : 'border-amber-200 bg-amber-50/40 hover:bg-amber-50'
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="font-bold text-gray-900">{app.quoteNumber} — {app.customerName}</span>
                  <span className="font-mono font-bold text-gray-900">${app.amount.toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between text-[11px] mt-1.5">
                  <span className="text-gray-600 font-medium">Rep: {app.salesRepName}</span>
                  <span className="px-2 py-0.5 rounded bg-white text-gray-800 border border-gray-200 font-semibold text-[10px]">
                    {role === 'SALES_REP' ? 'Awaiting Marcus Vance' : 'Requires L1 Sign-Off'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Operational Audit Feed */}
        <div className="bg-white rounded-xl border border-gray-100 p-5 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-gray-100 mb-3">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-gray-500" />
              <h3 className="text-sm font-bold text-gray-800">Governance Audit Trail</h3>
            </div>
            <span className="text-[11px] text-gray-400 font-mono">Immutable Log</span>
          </div>

          <div className="space-y-3">
            {auditLogs.slice(0, 3).map((log) => (
              <div key={log.id} className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 border border-gray-100 text-xs">
                <div className="w-7 h-7 rounded-md bg-blue-50 text-[#2563EB] flex items-center justify-center shrink-0 mt-0.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-gray-900 truncate">{log.userName} ({log.userRole})</span>
                    <span className="text-[10px] text-gray-400 font-mono shrink-0">
                      {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div className="text-gray-700 font-medium mt-0.5">{log.action}</div>
                  {log.reason && <p className="text-gray-500 text-[11px] mt-0.5">{log.reason}</p>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
