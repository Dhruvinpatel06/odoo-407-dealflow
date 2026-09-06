import React, { useState } from 'react';
import { 
  Search, 
  Filter, 
  LayoutGrid, 
  List, 
  Plus, 
  Building2, 
  Calendar, 
  User, 
  DollarSign, 
  TrendingUp, 
  ArrowRight,
  Sparkles
} from 'lucide-react';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/StatusBadge';
import { RiskBadge } from '../common/RiskBadge';
import { QuotationStage } from '../../types';
import { getRoleMeta } from '../../utils/rbac';
import { PaginationControls } from '../common/PaginationControls';

interface QuotationsListProps {
  initialViewMode?: 'table' | 'kanban';
}

export const QuotationsList: React.FC<QuotationsListProps> = ({ initialViewMode = 'table' }) => {
  const { 
    quotations, 
    setCurrentPage, 
    setSelectedQuoteId, 
    currentUser,
    createNewQuotation,
    showNotification 
  } = useApp();

  const [viewMode, setViewMode] = useState<'table' | 'kanban'>(initialViewMode);
  const [searchTerm, setSearchTerm] = useState('');
  const [stageFilter, setStageFilter] = useState<string>('ALL');
  const [scopeFilter, setScopeFilter] = useState<'MY_DEALS' | 'ALL_DEALS' | 'NEEDS_APPROVAL'>(
    currentUser.role === 'SALES_REP' ? 'MY_DEALS' : 'ALL_DEALS'
  );
  const [page, setPage] = useState<number>(1);
  const PAGE_SIZE = 4;

  const roleMeta = getRoleMeta(currentUser.role);

  const filteredQuotes = quotations.filter((q) => {
    const matchesSearch = 
      q.quoteNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.salesRepName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStage = stageFilter === 'ALL' || q.stage === stageFilter;
    
    let matchesScope = true;
    if (scopeFilter === 'MY_DEALS') {
      matchesScope = q.salesRepName === currentUser.name || q.salesRepName === 'Sarah Chen';
    } else if (scopeFilter === 'NEEDS_APPROVAL') {
      matchesScope = q.stage === 'PENDING_APPROVAL';
    }

    return matchesSearch && matchesStage && matchesScope;
  });

  const pagedQuotes = filteredQuotes.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const kanbanStages: { stage: QuotationStage; label: string; color: string }[] = [
    { stage: 'DRAFT', label: 'Draft', color: 'border-slate-300' },
    { stage: 'PENDING_APPROVAL', label: 'Pending Approval', color: 'border-amber-400' },
    { stage: 'APPROVED', label: 'Approved', color: 'border-emerald-400' },
    { stage: 'SENT', label: 'Sent to Customer', color: 'border-blue-400' },
    { stage: 'UNDER_NEGOTIATION', label: 'Under Negotiation', color: 'border-purple-400' },
    { stage: 'RETURNED_FOR_REVISION', label: 'Revision Required', color: 'border-orange-400' },
    { stage: 'CONFIRMED', label: 'Confirmed / Won', color: 'border-emerald-600' }
  ];

  const handleOpenQuote = (id: string) => {
    setSelectedQuoteId(id);
    setCurrentPage('quote-builder');
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 flex-1">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-[#111827] tracking-tight">Quotations & Deals Pipeline</h2>
          <p className="text-xs text-gray-500 mt-1">Manage B2B commercial quotes, track lifecycle stages, and enforce margin governance.</p>
        </div>

        <div className="flex items-center gap-3">
          {/* View Toggle */}
          <div className="bg-gray-100 p-1 rounded-lg flex items-center border border-gray-200">
            <button
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded-md transition cursor-pointer ${
                viewMode === 'table' ? 'bg-white text-gray-900 shadow-xs font-semibold' : 'text-gray-500 hover:text-gray-900'
              }`}
              title="Table View"
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('kanban')}
              className={`p-1.5 rounded-md transition cursor-pointer ${
                viewMode === 'kanban' ? 'bg-white text-gray-900 shadow-xs font-semibold' : 'text-gray-500 hover:text-gray-900'
              }`}
              title="Kanban Pipeline View"
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
          </div>

          {/* New Quote Button */}
          {(currentUser.role === 'SALES_REP' || currentUser.role === 'ADMIN' || currentUser.role === 'SALES_MANAGER') && (
            <button
              onClick={() => {
                createNewQuotation();
              }}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#2563EB] hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create Quotation</span>
            </button>
          )}
        </div>
      </div>

      {/* Role Context Notification Banner */}
      <div className={`p-4 rounded-xl border text-xs flex flex-wrap items-center justify-between gap-3 ${roleMeta.badgeColor}`}>
        <div className="flex items-center gap-2.5">
          <span className={`w-2.5 h-2.5 rounded-full ${roleMeta.badgeDot}`}></span>
          <span className="font-semibold text-gray-900">RBAC Active: {roleMeta.label} ({currentUser.name})</span>
          <span className="text-gray-600 hidden md:inline">&bull; {roleMeta.desc}</span>
        </div>
        <span className="font-mono text-[11px] font-bold opacity-85">
          {currentUser.role === 'SALES_REP' && 'Discretion Ceiling: ≤ 10%'}
          {currentUser.role === 'SALES_MANAGER' && 'Approval Authority: ≤ 20%'}
          {currentUser.role === 'FINANCE_OPERATIONS' && 'Gross Margin Floor: ≥ 30%'}
          {currentUser.role === 'ADMIN' && 'Full Governance Policy Control'}
        </span>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-sm flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3 flex-1 min-w-[260px]">
          {/* Scope Filter Pills */}
          <div className="inline-flex bg-gray-100 p-0.5 rounded-lg border border-gray-200 text-xs">
            {currentUser.role === 'SALES_REP' && (
              <button
                onClick={() => { setScopeFilter('MY_DEALS'); setPage(1); }}
                className={`px-3 py-1 rounded-md font-semibold transition cursor-pointer ${
                  scopeFilter === 'MY_DEALS' ? 'bg-white text-gray-900 shadow-2xs' : 'text-gray-500 hover:text-gray-800'
                }`}
              >
                My Accounts
              </button>
            )}
            <button
              onClick={() => { setScopeFilter('ALL_DEALS'); setPage(1); }}
              className={`px-3 py-1 rounded-md font-semibold transition cursor-pointer ${
                scopeFilter === 'ALL_DEALS' ? 'bg-white text-gray-900 shadow-2xs' : 'text-gray-500 hover:text-gray-800'
              }`}
            >
              All Quotes ({quotations.length})
            </button>
            <button
              onClick={() => { setScopeFilter('NEEDS_APPROVAL'); setPage(1); }}
              className={`px-3 py-1 rounded-md font-semibold transition cursor-pointer ${
                scopeFilter === 'NEEDS_APPROVAL' ? 'bg-white text-purple-700 shadow-2xs' : 'text-gray-500 hover:text-gray-800'
              }`}
            >
              Needs Approval ({quotations.filter(q => q.stage === 'PENDING_APPROVAL').length})
            </button>
          </div>

          <div className="relative flex-1 min-w-[180px]">
            <Search className="w-3.5 h-3.5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by quote number, customer, or sales owner..."
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-gray-50 border border-gray-200 rounded-lg text-gray-800 placeholder-gray-400 focus:outline-hidden focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <select
            value={stageFilter}
            onChange={(e) => { setStageFilter(e.target.value); setPage(1); }}
            className="text-xs bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 text-gray-700 font-medium focus:ring-2 focus:ring-blue-500 focus:outline-hidden cursor-pointer"
          >
            <option value="ALL">All Stages ({quotations.length})</option>
            <option value="DRAFT">Draft</option>
            <option value="PENDING_APPROVAL">Pending Approval</option>
            <option value="APPROVED">Approved</option>
            <option value="SENT">Sent</option>
            <option value="UNDER_NEGOTIATION">Under Negotiation</option>
            <option value="RETURNED_FOR_REVISION">Returned for Revision</option>
            <option value="CONFIRMED">Confirmed</option>
          </select>
        </div>

        <div className="text-xs text-gray-500">
          Showing <strong className="text-gray-900">{filteredQuotes.length}</strong> of {quotations.length} deals
        </div>
      </div>

      {/* TABLE VIEW */}
      {viewMode === 'table' ? (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-gray-50 text-[11px] uppercase tracking-wider text-gray-500 font-semibold border-b border-gray-100">
                  <th className="px-5 py-3">Quote Number</th>
                  <th className="px-5 py-3">Customer</th>
                  <th className="px-5 py-3">Stage</th>
                  <th className="px-5 py-3">Amount</th>
                  <th className="px-5 py-3 text-center">Margin</th>
                  <th className="px-5 py-3 text-center">Risk Assessment</th>
                  <th className="px-5 py-3">Owner</th>
                  <th className="px-5 py-3">Date</th>
                  <th className="px-5 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="text-sm divide-y divide-gray-100">
                {pagedQuotes.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-gray-400 text-xs">
                      No quotations found matching the filters.
                    </td>
                  </tr>
                ) : (
                  pagedQuotes.map((quote) => (
                    <tr
                      key={quote.id}
                      onClick={() => handleOpenQuote(quote.id)}
                      className="hover:bg-gray-50 transition-colors cursor-pointer"
                    >
                      <td className="px-5 py-4 font-mono text-xs text-gray-400 font-medium">{quote.quoteNumber}</td>
                      <td className="px-5 py-4">
                        <div className="font-bold text-gray-900">{quote.customerName}</div>
                        <div className="text-[10px] text-gray-400 font-mono">Tier: {quote.customerTier}</div>
                      </td>
                      <td className="px-5 py-4">
                        <StatusBadge status={quote.stage} />
                      </td>
                      <td className="px-5 py-4 font-mono font-bold text-gray-900">
                        ${quote.totalAmount.toLocaleString()}
                      </td>
                      <td className="px-5 py-4 text-center font-mono font-medium text-emerald-600">
                        {quote.blendedMarginPercent}%
                      </td>
                      <td className="px-5 py-4 text-center">
                        <RiskBadge score={quote.blendedRiskScore} status={quote.riskStatus} />
                      </td>
                      <td className="px-5 py-4 text-gray-600 text-xs">{quote.salesRepName}</td>
                      <td className="px-5 py-4 text-gray-400 font-mono text-xs">
                        {new Date(quote.updatedAt).toLocaleDateString()}
                      </td>
                      <td className="px-5 py-4 text-right">
                        {currentUser.role === 'SALES_MANAGER' && quote.stage === 'PENDING_APPROVAL' ? (
                          <button className="px-2.5 py-1 rounded bg-purple-600 hover:bg-purple-700 text-white font-bold text-[11px] inline-flex items-center gap-1 cursor-pointer shadow-2xs">
                            <span>Sign Off (L1)</span>
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        ) : currentUser.role === 'FINANCE_OPERATIONS' && quote.stage === 'PENDING_APPROVAL' ? (
                          <button className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[11px] inline-flex items-center gap-1 cursor-pointer shadow-2xs">
                            <span>Finance Review</span>
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        ) : (
                          <button className="text-[#2563EB] hover:text-blue-800 font-semibold text-xs inline-flex items-center gap-1 cursor-pointer">
                            <span>Open</span>
                            <ArrowRight className="w-3 h-3" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <PaginationControls
            currentPage={page}
            totalItems={filteredQuotes.length}
            pageSize={PAGE_SIZE}
            onPageChange={setPage}
          />
        </div>
      ) : (
        /* KANBAN / PIPELINE VIEW */
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4 overflow-x-auto pb-4">
          {kanbanStages.map((col) => {
            const colQuotes = filteredQuotes.filter((q) => q.stage === col.stage);
            const colTotal = colQuotes.reduce((acc, q) => acc + q.totalAmount, 0);

            return (
              <div key={col.stage} className="bg-gray-50 rounded-xl p-4 border border-gray-200/80 min-w-[240px]">
                {/* Stage Header */}
                <div className="flex items-center justify-between pb-2 mb-3 border-b border-gray-200">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-bold text-gray-800">{col.label}</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-gray-200 text-gray-700 font-bold font-mono">
                      {colQuotes.length}
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-gray-500 font-medium">
                    ${Math.round(colTotal).toLocaleString()}
                  </span>
                </div>

                {/* Cards List */}
                <div className="space-y-2.5">
                  {colQuotes.length === 0 ? (
                    <div className="py-6 text-center text-gray-400 text-xs italic">
                      No quotations
                    </div>
                  ) : (
                    colQuotes.map((q) => (
                      <div
                        key={q.id}
                        onClick={() => handleOpenQuote(q.id)}
                        className="bg-white rounded-lg p-3 border border-gray-100 shadow-sm hover:shadow-md transition cursor-pointer hover:border-gray-300"
                      >
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="font-mono font-bold text-[#2563EB]">{q.quoteNumber}</span>
                          <span className="font-mono font-bold text-gray-900">${q.totalAmount.toLocaleString()}</span>
                        </div>
                        <div className="text-xs font-semibold text-gray-800 truncate">{q.customerName}</div>
                        
                        <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-100 text-[10px]">
                          <span className="text-gray-500 font-mono">Margin: <strong className="text-green-600">{q.blendedMarginPercent}%</strong></span>
                          <RiskBadge score={q.blendedRiskScore} status={q.riskStatus} showScore={false} />
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
