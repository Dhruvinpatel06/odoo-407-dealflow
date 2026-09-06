import React, { useState } from 'react';
import { 
  CheckCircle2, 
  RotateCcw, 
  AlertTriangle, 
  Clock, 
  Check, 
  X, 
  FileText,
  ShieldAlert, 
  Lock,
  Loader2
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useApp } from '../../context/AppContext';
import { StatusBadge } from '../common/StatusBadge';
import { RiskBadge } from '../common/RiskBadge';
import { AccessRestrictedView } from '../common/AccessRestrictedView';
import { PaginationControls } from '../common/PaginationControls';
import { 
  useApprovalsQuery, 
  useApprovalAuditLogQuery, 
  useApproveStepMutation, 
  useRejectApprovalMutation, 
  useReturnForRevisionMutation 
} from '../../hooks/useBackendData';
import type { ApprovalStepResponse } from '../../services/approvalService';

export const ApprovalCenter: React.FC = () => {
  const { 
    currentUser, 
    setCurrentPage, 
    setSelectedQuoteId, 
    showNotification 
  } = useApp();

  const queryClient = useQueryClient();

  // If customer attempts to access internal approval center
  if (currentUser.role === 'CUSTOMER_PORTAL' || currentUser.role === 'CUSTOMER') {
    return (
      <AccessRestrictedView 
        requiredRole="Sales Manager, Finance, or Admin" 
        featureName="Internal Approval Center & Discount Governance" 
      />
    );
  }

  const [selectedApprovalId, setSelectedApprovalId] = useState<string>('');
  const [decisionReason, setDecisionReason] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const PAGE_SIZE = 4;

  const { data: rawApprovals = [], isLoading } = useApprovalsQuery();
  const approveMutation = useApproveStepMutation();
  const rejectMutation = useRejectApprovalMutation();
  const returnMutation = useReturnForRevisionMutation();

  const approvals = rawApprovals;
  const pagedApprovals = approvals.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const activeApproval: any = approvals.find((a: any) => a.id === selectedApprovalId) || approvals[0];
  const activeApprovalId = activeApproval?.id;
  const { data: auditLog = [] } = useApprovalAuditLogQuery(activeApprovalId || '');

  // RBAC Permission check for approval actions:
  // - Admin can approve any step
  // - Sales Manager can approve if current step is SALES_MANAGER
  // - Finance can approve if current step is FINANCE_OPERATIONS
  // - Sales Rep CANNOT approve any step (strictly view-only submitter tracking)
  const pendingStep = (activeApproval?.steps || []).find((s: any) => s.status === 'PENDING');
  const isManagerStep = pendingStep?.role_required === 'SALES_MANAGER' || pendingStep?.roleRequired === 'SALES_MANAGER';
  const isFinanceStep = pendingStep?.role_required === 'FINANCE_OPERATIONS' || pendingStep?.roleRequired === 'FINANCE_OPERATIONS';

  const canApprove = 
    currentUser.role === 'ADMIN' ||
    (currentUser.role === 'SALES_MANAGER' && isManagerStep) ||
    (currentUser.role === 'FINANCE_OPERATIONS' && isFinanceStep);

  const handleApprove = () => {
    if (!activeApprovalId) return;
    approveMutation.mutate(
      { id: activeApprovalId, payload: { comment: decisionReason || 'Commercial terms verified. Approved under discount governance discretion.' } },
      {
        onSuccess: () => {
          showNotification('Approval step approved successfully', 'success');
          setDecisionReason('');
        },
        onError: (err: any) => {
          showNotification(err?.message || 'Failed to approve step', 'error');
        }
      }
    );
  };

  const handleReject = () => {
    if (!activeApprovalId) return;
    rejectMutation.mutate(
      { id: activeApprovalId, payload: { comment: decisionReason || 'Discount exceeds maximum corporate margin tolerance without offsetting commitment.' } },
      {
        onSuccess: () => {
          showNotification('Approval rejected', 'info');
          setDecisionReason('');
        },
        onError: (err: any) => {
          showNotification(err?.message || 'Failed to reject deal', 'error');
        }
      }
    );
  };

  const handleReturnForRevision = () => {
    if (!activeApprovalId) return;
    returnMutation.mutate(
      { id: activeApprovalId, payload: { comment: decisionReason || 'Please reduce services discount or adjust parameters before resubmitting.' } },
      {
        onSuccess: () => {
          showNotification('Quotation returned for revision', 'info');
          setDecisionReason('');
        },
        onError: (err: any) => {
          showNotification(err?.message || 'Failed to return for revision', 'error');
        }
      }
    );
  };

  if (isLoading) {
    return (
      <div className="p-16 flex flex-col items-center justify-center text-slate-500 gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
        <span className="text-xs font-medium">Loading approval workflows...</span>
      </div>
    );
  }

  const pendingCount = approvals.filter((a: any) => a.status === 'PENDING').length;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 flex-1">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-[#111827] tracking-tight">Governance & Approval Center</h2>
        <p className="text-sm text-gray-500 mt-1">Automated multi-tier approval routing for quotes exceeding discount ceilings or risk thresholds.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (5 Cols): Approval Workflows List */}
        <div className="lg:col-span-5 space-y-3">
          <div className="bg-white rounded-xl border border-gray-100 p-4 shadow-xs">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-gray-100">
              <span className="text-xs font-bold text-gray-700 uppercase tracking-wider">
                Approval Workflows ({approvals.length})
              </span>
              <span className="text-[10px] text-amber-700 font-bold bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded-full">
                {pendingCount} Pending
              </span>
            </div>

            <div className="space-y-2.5">
              {pagedApprovals.map((app: any) => {
                const isSelected = app.id === (activeApproval?.id || selectedApprovalId);
                const quoteNum = app.quotation_number || app.quoteNumber || 'Quote';
                const custName = app.customer_name || app.customerName || 'Customer';
                const totalAmt = Number(app.total_amount ?? app.amount ?? 0);
                const rScore = Number(app.risk_score ?? app.riskScore ?? 0);
                const stepsCount = (app.steps || []).length;
                return (
                  <div
                    key={app.id}
                    onClick={() => setSelectedApprovalId(app.id)}
                    className={`p-4 rounded-lg border transition cursor-pointer ${
                      isSelected
                        ? 'border-[#2563EB] bg-blue-50/40 shadow-xs'
                        : 'border-gray-200 bg-white hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-mono font-bold text-[#2563EB]">{quoteNum}</span>
                      <StatusBadge status={app.status} />
                    </div>
                    <div className="text-xs font-bold text-gray-900">{custName}</div>
                    
                    <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-gray-100 text-[11px]">
                      <span className="font-mono font-bold text-gray-800">${totalAmt.toLocaleString()}</span>
                      <RiskBadge score={rScore} />
                    </div>

                    {/* Step indicator */}
                    <div className="mt-2 text-[10px] text-gray-500 flex items-center gap-1 font-mono">
                      <span>Chain:</span>
                      <strong className="text-gray-700">
                        {stepsCount === 1 ? 'Manager Only' : 'Manager → Finance'}
                      </strong>
                    </div>
                  </div>
                );
              })}
            </div>

            <PaginationControls
              currentPage={page}
              totalItems={approvals.length}
              pageSize={PAGE_SIZE}
              onPageChange={setPage}
              className="mt-3 rounded-lg border border-gray-100"
            />
          </div>
        </div>

        {/* Right Column (7 Cols): Approval Detail & Action View */}
        {activeApproval ? (
          <div className="lg:col-span-7 space-y-5">
            {/* Approval Detail Card */}
            <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-xs space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-gray-100">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-bold text-[#111827]">{activeApproval.quotation_number}</h3>
                    <StatusBadge status={activeApproval.status} />
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    Customer: <strong className="text-gray-800">{activeApproval.customer_name || 'Customer'}</strong> • Submitted: {new Date(activeApproval.created_at).toLocaleString()}
                  </div>
                </div>

                <button
                  onClick={() => {
                    setSelectedQuoteId(activeApproval.quotation_id);
                    setCurrentPage('quote-builder');
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 text-xs font-semibold text-[#2563EB] transition cursor-pointer"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>Inspect Quote Lines</span>
                </button>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-3 p-4 rounded-lg bg-gray-50 border border-gray-100">
                <div>
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Total Deal Value</p>
                  <div className="text-lg font-bold font-mono text-[#111827] mt-1">
                    ${Number(activeApproval.total_amount || 0).toLocaleString()}
                  </div>
                </div>
                <div>
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Blended Risk Score</p>
                  <div className="mt-1">
                    <RiskBadge score={Number(activeApproval.risk_score || 0)} />
                  </div>
                </div>
              </div>

              {/* Breaches */}
              {(activeApproval.reasons || []).length > 0 && (
                <div>
                  <div className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-red-500" />
                    <span>Why Approval is Required</span>
                  </div>
                  <div className="space-y-2">
                    {activeApproval.reasons!.map((r: string, i: number) => (
                      <div key={i} className="p-3 rounded-lg bg-red-50/50 border border-red-200/70 text-xs text-red-900 leading-relaxed">
                        {r}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Sequential Approval Chain */}
              <div>
                <div className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-3 flex items-center justify-between">
                  <span>Sequential Approval Chain</span>
                  <span className="text-[10px] text-gray-400 font-mono">System Directed</span>
                </div>

                <div className="space-y-2.5">
                  {(activeApproval.steps || []).map((step: ApprovalStepResponse, idx: number) => {
                    const isPending = step.status === 'PENDING';
                    const isApproved = step.status === 'APPROVED';

                    return (
                      <div
                        key={step.id || idx}
                        className={`p-3.5 rounded-lg border flex items-center justify-between text-xs ${
                          isPending 
                            ? 'bg-amber-50/40 border-amber-200' 
                            : isApproved 
                            ? 'bg-green-50/40 border-green-200' 
                            : 'bg-gray-50 border-gray-200'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-xs font-mono ${
                            isApproved ? 'bg-green-600 text-white' : isPending ? 'bg-amber-500 text-white' : 'bg-gray-300 text-gray-700'
                          }`}>
                            {idx + 1}
                          </div>
                          <div>
                            <div className="font-bold text-gray-900">
                              {step.role_required === 'SALES_MANAGER' ? 'Level 1: Sales Manager Review' : 'Level 2: Finance & Revenue Operations'}
                            </div>
                            <div className="text-[11px] text-gray-500 mt-0.5">
                              Reviewer: <span className="font-medium text-gray-700">{step.reviewer_name || step.role_required}</span>
                            </div>
                            {step.comment && (
                              <p className="text-[11px] text-gray-600 mt-1 italic">"{step.comment}"</p>
                            )}
                          </div>
                        </div>

                        <StatusBadge status={step.status} />
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Reviewer Action Form */}
              {activeApproval.status === 'PENDING' && (
                <>
                  {currentUser.role === 'SALES_REP' ? (
                    <div className="pt-4 border-t border-gray-100">
                      <div className="p-4 rounded-xl bg-blue-50/70 border border-blue-200">
                        <div className="flex items-start gap-3">
                          <ShieldAlert className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="text-xs font-bold text-gray-900">
                                Submitter Tracking Mode &bull; {currentUser.name} (Sales Rep)
                              </h4>
                              <span className="px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 text-[10px] font-bold">
                                Read Only
                              </span>
                            </div>
                            <p className="text-[11px] text-gray-600 mt-1 leading-relaxed">
                              DealFlow360 RBAC governance strictly restricts sales representatives from self-approving discount concessions. 
                              This quote is currently awaiting review by authorized management.
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : !canApprove ? (
                    <div className="pt-4 border-t border-gray-100">
                      <div className="p-4 rounded-xl bg-gray-50 border border-gray-200 text-xs">
                        <div className="flex items-center gap-2 text-gray-700 font-semibold mb-1">
                          <Lock className="w-3.5 h-3.5 text-gray-400" />
                          <span>Awaiting Stage Authorization</span>
                        </div>
                        <p className="text-[11px] text-gray-500">
                          {isFinanceStep && currentUser.role === 'SALES_MANAGER'
                            ? 'Sales Manager review is complete. This deal is currently in Finance queue for final commercial validation.'
                            : 'This step requires approval from another assigned role.'}
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="pt-4 border-t border-gray-100 space-y-3">
                      <div className="flex items-center justify-between">
                        <label className="block text-xs font-bold text-gray-900">
                          {currentUser.role === 'SALES_MANAGER' && 'Level 1 Manager Sign-Off & Audit Rationale:'}
                          {currentUser.role === 'FINANCE_OPERATIONS' && 'Level 2 Finance Risk & Margin Validation:'}
                          {currentUser.role === 'ADMIN' && 'Administrative Governance Decision:'}
                        </label>
                        <span className="text-[10px] text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                          Signer: {currentUser.name}
                        </span>
                      </div>

                      <textarea
                        rows={2}
                        value={decisionReason}
                        onChange={(e) => setDecisionReason(e.target.value)}
                        placeholder="Enter approval rationale or revision condition for immutable audit log..."
                        className="w-full text-xs p-3 rounded-lg border border-gray-200 focus:outline-hidden focus:ring-2 focus:ring-blue-500 bg-gray-50 focus:bg-white transition"
                      />

                      <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
                        <button
                          onClick={handleReturnForRevision}
                          disabled={returnMutation.isPending}
                          className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-800 text-xs font-semibold transition cursor-pointer disabled:opacity-50"
                        >
                          <RotateCcw className="w-3.5 h-3.5 text-amber-600" />
                          <span>Return for Revision</span>
                        </button>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={handleReject}
                            disabled={rejectMutation.isPending}
                            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-red-300 bg-red-50 hover:bg-red-100 text-red-800 text-xs font-semibold transition cursor-pointer disabled:opacity-50"
                          >
                            <X className="w-3.5 h-3.5 text-red-600" />
                            <span>Reject Deal</span>
                          </button>

                          <button
                            onClick={handleApprove}
                            disabled={approveMutation.isPending}
                            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-white text-xs font-bold shadow-xs transition cursor-pointer disabled:opacity-50 ${
                              currentUser.role === 'SALES_MANAGER'
                                ? 'bg-purple-600 hover:bg-purple-700'
                                : 'bg-green-600 hover:bg-green-700'
                            }`}
                          >
                            <Check className="w-3.5 h-3.5" />
                            <span>Approve Step</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}

              {/* Audit Timeline */}
              <div className="pt-4 border-t border-gray-100">
                <div className="text-[11px] font-bold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-1">
                  <Clock className="w-3 h-3 text-gray-400" />
                  <span>Audit Timeline</span>
                </div>
                {auditLog.length === 0 ? (
                  <p className="text-xs text-gray-400">No recorded audit events for this approval workflow.</p>
                ) : (
                  <div className="space-y-2">
                    {auditLog.map((item: any, idx: number) => (
                      <div key={item.id || idx} className="p-3 rounded-md bg-gray-50 border border-gray-100 text-xs flex items-start gap-2.5">
                        <div className="w-5 h-5 rounded bg-blue-100 text-blue-700 flex items-center justify-center shrink-0 mt-0.5">
                          <CheckCircle2 className="w-3 h-3" />
                        </div>
                        <div>
                          <div className="font-semibold text-gray-800">
                            {item.user_name || 'System'} ({item.user_role || 'Policy Engine'}) — <span className="font-mono text-[10px] text-gray-400">{item.created_at ? new Date(item.created_at).toLocaleString() : ''}</span>
                          </div>
                          <div className="text-gray-600 text-[11px] mt-0.5">{item.action || item.event_type}</div>
                          {(item.comment || item.reason) && <p className="text-gray-500 text-[11px] mt-0.5 italic">"{item.comment || item.reason}"</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="lg:col-span-7 bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-500 text-xs">
            Select an approval workflow from the left list.
          </div>
        )}
      </div>
    </div>
  );
};
