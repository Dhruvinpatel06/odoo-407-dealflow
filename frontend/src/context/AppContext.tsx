import React, { createContext, useContext, useState } from 'react';
import { 
  User, 
  UserRole, 
  Quotation, 
  QuotationLine, 
  Product, 
  ApprovalInstance, 
  OrderFulfillment, 
  Invoice, 
  SubscriptionItem, 
  DealAlert, 
  Recommendation,
  AuditLog
} from '../types';
import { 
  mockUsers, 
  mockQuotations, 
  mockProducts, 
  mockApprovals, 
  mockFulfillments, 
  mockSubscriptions, 
  mockInvoices, 
  mockDealAlerts, 
  mockRecommendations 
} from '../mockData';

interface AppContextType {
  currentUser: User;
  setCurrentUser: (user: User) => void;
  setUserRole: (role: UserRole) => void;
  currentPage: string;
  setCurrentPage: (page: string) => void;
  selectedQuoteId: string;
  setSelectedQuoteId: (id: string) => void;
  
  // Data
  quotations: Quotation[];
  activeQuotation: Quotation | undefined;
  products: Product[];
  approvals: ApprovalInstance[];
  fulfillments: Record<string, OrderFulfillment>;
  subscriptions: SubscriptionItem[];
  invoices: Invoice[];
  dealAlerts: DealAlert[];
  recommendations: Recommendation[];
  auditLogs: AuditLog[];
  
  // Actions
  updateLineQuantity: (lineId: string, delta: number) => void;
  updateLineDiscount: (lineId: string, discountPercent: number) => void;
  addProductToActiveQuote: (productId: string) => void;
  removeLineFromQuote: (lineId: string) => void;
  addRecommendationToQuote: (recommendation: Recommendation) => void;
  dismissRecommendation: (productId: string) => void;
  recalculateActiveQuote: () => void;
  submitActiveQuoteForApproval: () => void;
  confirmActiveQuote: () => void;
  
  // Approvals
  approveCurrentStep: (approvalId: string, comment?: string) => void;
  rejectApproval: (approvalId: string, reason: string) => void;
  returnForRevision: (approvalId: string, reason: string) => void;
  
  // Fulfillment
  acceptSuggestedSplit: (orderId: string) => void;
  overrideAllocation: (orderId: string, newAllocations: any[]) => void;
  consolidateBackorder: (orderId: string) => void;
  
  // Billing
  recordPayment: (invoiceId: string, amount: number) => void;
  modifySubscription: (subId: string, deltaQty: number) => void;
  
  // Portal Negotiation
  submitCustomerNegotiation: (quoteId: string, counterDiscount: number, notes: string) => void;
  customerConfirmQuote: (quoteId: string) => void;
  
  // Health
  acknowledgeAlert: (alertId: string) => void;
  resolveAlert: (alertId: string) => void;
  triggerAlertNudge: (alertId: string) => void;
  
  // Notifications
  notification: { message: string; type: 'success' | 'warning' | 'info' | 'error' } | null;
  showNotification: (message: string, type?: 'success' | 'warning' | 'info' | 'error') => void;
  
  // Quick test flow guide modal
  isGuideOpen: boolean;
  setIsGuideOpen: (open: boolean) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<User>(mockUsers[0]); // Default Sales Rep Sarah Chen
  const [currentPage, setCurrentPage] = useState<string>('dashboard');
  const [selectedQuoteId, setSelectedQuoteId] = useState<string>('q-1048');
  
  const [quotations, setQuotations] = useState<Quotation[]>(mockQuotations);
  const [products] = useState<Product[]>(mockProducts);
  const [approvals, setApprovals] = useState<ApprovalInstance[]>(mockApprovals);
  const [fulfillments, setFulfillments] = useState<Record<string, OrderFulfillment>>(mockFulfillments);
  const [subscriptions, setSubscriptions] = useState<SubscriptionItem[]>(mockSubscriptions);
  const [invoices, setInvoices] = useState<Invoice[]>(mockInvoices);
  const [dealAlerts, setDealAlerts] = useState<DealAlert[]>(mockDealAlerts);
  const [recommendations, setRecommendations] = useState<Recommendation[]>(mockRecommendations);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([
    {
      id: 'aud-init-1',
      entityType: 'QUOTATION',
      entityId: 'q-1048',
      userName: 'Sarah Chen',
      userRole: 'Sales Representative',
      action: 'RECALCULATED_MARGIN',
      timestamp: '2026-09-04T16:40:00Z',
      details: 'Discount governance evaluation flagged 18% services discount exceeding 8% ceiling.'
    },
    {
      id: 'aud-init-2',
      entityType: 'APPROVAL',
      entityId: 'app-1',
      userName: 'System Governance Engine',
      userRole: 'Automated Rule Evaluator',
      action: 'AUTO_ROUTED_APPROVAL',
      timestamp: '2026-09-04T16:45:00Z',
      reason: 'Blended risk score 72 > 70 threshold triggers sequential Manager -> Finance approval.'
    }
  ]);

  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'warning' | 'info' | 'error' } | null>(null);
  const [isGuideOpen, setIsGuideOpen] = useState<boolean>(false);

  const showNotification = (message: string, type: 'success' | 'warning' | 'info' | 'error' = 'info') => {
    setNotification({ message, type });
    setTimeout(() => {
      setNotification(null);
    }, 4500);
  };

  const setUserRole = (role: UserRole) => {
    const userMatch = mockUsers.find(u => u.role === role) || {
      ...currentUser,
      role
    };
    setCurrentUser(userMatch);
    if (role === 'CUSTOMER_PORTAL') {
      setCurrentPage('portal');
      showNotification(`Switched role to Customer Portal (${userMatch.name} - Acme Corp)`, 'info');
    } else {
      if (currentPage === 'portal') {
        setCurrentPage('dashboard');
      }
      showNotification(`Switched active persona to ${userMatch.role.replace('_', ' ')} (${userMatch.name})`, 'info');
    }
  };

  const activeQuotation = quotations.find(q => q.id === selectedQuoteId) || quotations[0];

  // Recalculate quotation according to authoritative business governance rules
  const recalculateHelper = (quote: Quotation): Quotation => {
    let subtotal = 0;
    let totalCost = 0;
    let totalDiscountAmount = 0;
    let taxAmount = 0;
    let maxExcessPoints = 0;
    let sumExcessPoints = 0;
    const reasons: string[] = [];

    const updatedLines = quote.lines.map(line => {
      const prod = products.find(p => p.id === line.productId);
      const unitPrice = line.unitPrice;
      const unitCost = line.unitCost;
      const qty = line.quantity;
      const disc = Math.max(0, Math.min(100, line.discountPercent));

      // Ceiling is minimum of customer tier ceiling and category ceiling
      const ceiling = Math.min(quote.customerTier === 'GOLD' ? 15 : quote.customerTier === 'SILVER' ? 10 : quote.customerTier === 'PLATINUM' ? 20 : 5, prod ? prod.categoryDiscountCeiling : 10);
      const excess = Math.max(0, disc - ceiling);

      if (excess > 0) {
        maxExcessPoints = Math.max(maxExcessPoints, excess);
        sumExcessPoints += excess;
        reasons.push(`${line.productName} discount (${disc}%) exceeds ${line.category.toLowerCase()} ceiling (${ceiling}%) by +${excess.toFixed(1)}%`);
      }

      const grossLine = unitPrice * qty;
      const discAmount = grossLine * (disc / 100);
      const netLine = grossLine - discAmount;
      const costLine = unitCost * qty;
      const lineMargin = netLine > 0 ? ((netLine - costLine) / netLine) * 100 : 0;

      subtotal += netLine;
      totalCost += costLine;
      totalDiscountAmount += discAmount;

      const taxRate = prod ? prod.taxRate : 0.08;
      taxAmount += netLine * taxRate;

      return {
        ...line,
        allowedDiscountCeiling: ceiling,
        discountExcessPercent: excess,
        lineTotal: Math.round(netLine * 100) / 100,
        marginPercent: Math.round(lineMargin * 10) / 10
      };
    });

    const totalAmount = subtotal + taxAmount;
    const blendedMargin = subtotal > 0 ? ((subtotal - totalCost) / subtotal) * 100 : 0;

    // Blended risk score calculation (0 to 100)
    // Formula combines:
    // 1) Maximum single line violation
    // 2) Aggregate pattern of small violations across multiple lines
    // 3) Low margin penalty
    let riskScore = 15; // Base healthy score
    if (sumExcessPoints > 0) {
      riskScore += Math.round(maxExcessPoints * 3.5 + (sumExcessPoints - maxExcessPoints) * 2.0);
    }
    if (blendedMargin < 25) {
      riskScore += 18;
      reasons.push(`Blended deal margin (${blendedMargin.toFixed(1)}%) is below recommended 25% guideline.`);
    } else if (blendedMargin < 35) {
      riskScore += 8;
    }
    riskScore = Math.min(98, Math.max(10, riskScore));

    const riskStatus = riskScore >= 70 ? 'HIGH_RISK' : riskScore >= 45 ? 'MODERATE' : 'HEALTHY';
    const approvalRequired = riskScore >= 45;
    const requiredApprovalLevel = riskScore >= 70 ? 'MANAGER_AND_FINANCE' : riskScore >= 45 ? 'SALES_MANAGER' : 'NONE';

    if (riskScore >= 70) {
      reasons.push('Blended risk exceeds 70: triggers sequential 2-tier approval (Sales Manager -> Finance).');
    } else if (riskScore >= 45) {
      reasons.push('Blended risk exceeds 45: requires Sales Manager approval.');
    } else {
      reasons.push('All parameters within standard limits. No approval required.');
    }

    return {
      ...quote,
      lines: updatedLines,
      subtotal: Math.round(subtotal * 100) / 100,
      totalDiscountAmount: Math.round(totalDiscountAmount * 100) / 100,
      taxAmount: Math.round(taxAmount * 100) / 100,
      totalAmount: Math.round(totalAmount * 100) / 100,
      totalCost: Math.round(totalCost * 100) / 100,
      blendedMarginPercent: Math.round(blendedMargin * 10) / 10,
      blendedRiskScore: riskScore,
      riskStatus,
      riskReasons: reasons,
      approvalRequired,
      requiredApprovalLevel,
      updatedAt: new Date().toISOString()
    };
  };

  const updateLineQuantity = (lineId: string, delta: number) => {
    setQuotations(prev => prev.map(q => {
      if (q.id !== selectedQuoteId) return q;
      const updatedLines = q.lines.map(line => {
        if (line.id === lineId) {
          const newQty = Math.max(1, line.quantity + delta);
          return { ...line, quantity: newQty };
        }
        return line;
      });
      const recalculated = recalculateHelper({ ...q, lines: updatedLines });
      return recalculated;
    }));
  };

  const updateLineDiscount = (lineId: string, discountPercent: number) => {
    setQuotations(prev => prev.map(q => {
      if (q.id !== selectedQuoteId) return q;
      const updatedLines = q.lines.map(line => {
        if (line.id === lineId) {
          return { ...line, discountPercent: Math.max(0, Math.min(100, discountPercent)) };
        }
        return line;
      });
      const recalculated = recalculateHelper({ ...q, lines: updatedLines });
      return recalculated;
    }));
  };

  const addProductToActiveQuote = (productId: string) => {
    const prod = products.find(p => p.id === productId);
    if (!prod) return;

    setQuotations(prev => prev.map(q => {
      if (q.id !== selectedQuoteId) return q;
      const existing = q.lines.find(l => l.productId === productId);
      let updatedLines: QuotationLine[];
      if (existing) {
        updatedLines = q.lines.map(l => l.productId === productId ? { ...l, quantity: l.quantity + 1 } : l);
      } else {
        const newLine: QuotationLine = {
          id: `ql-${Date.now()}`,
          productId: prod.id,
          productName: prod.name,
          category: prod.category,
          quantity: 1,
          unitPrice: prod.unitPrice,
          unitCost: prod.unitCost,
          discountPercent: 0,
          allowedDiscountCeiling: prod.categoryDiscountCeiling,
          discountExcessPercent: 0,
          lineTotal: prod.unitPrice,
          marginPercent: ((prod.unitPrice - prod.unitCost) / prod.unitPrice) * 100,
          isSubscription: prod.isSubscriptionEligible,
          recurringInterval: prod.recurringInterval
        };
        updatedLines = [...q.lines, newLine];
      }
      const recalculated = recalculateHelper({ ...q, lines: updatedLines });
      return recalculated;
    }));
    showNotification(`Added ${prod.name} to Quotation ${activeQuotation.quoteNumber}`, 'success');
  };

  const removeLineFromQuote = (lineId: string) => {
    setQuotations(prev => prev.map(q => {
      if (q.id !== selectedQuoteId) return q;
      const updatedLines = q.lines.filter(l => l.id !== lineId);
      return recalculateHelper({ ...q, lines: updatedLines });
    }));
    showNotification(`Removed product line from quotation`, 'info');
  };

  const addRecommendationToQuote = (rec: Recommendation) => {
    addProductToActiveQuote(rec.productId);
    setRecommendations(prev => prev.filter(r => r.productId !== rec.productId));
    showNotification(`Added ${rec.productName} (${rec.promotionTag || 'Recommendation'}) — Margin impact +${rec.marginDelta}%`, 'success');
  };

  const dismissRecommendation = (productId: string) => {
    setRecommendations(prev => prev.filter(r => r.productId !== productId));
    showNotification(`Dismissed recommendation`, 'info');
  };

  const recalculateActiveQuote = () => {
    setQuotations(prev => prev.map(q => {
      if (q.id !== selectedQuoteId) return q;
      return recalculateHelper(q);
    }));
    showNotification(`Deal terms and margin recalculated with backend governance rules`, 'info');
  };

  const submitActiveQuoteForApproval = () => {
    const current = activeQuotation;
    const recalculated = recalculateHelper(current);

    if (recalculated.approvalRequired) {
      const steps = [];
      if (recalculated.requiredApprovalLevel === 'MANAGER_AND_FINANCE') {
        steps.push(
          {
            id: `step-${Date.now()}-1`,
            stepNumber: 1,
            roleRequired: 'SALES_MANAGER' as const,
            reviewerName: 'Marcus Vance',
            status: 'PENDING' as const,
            comment: 'Awaiting Manager review for discount ceiling violation.'
          },
          {
            id: `step-${Date.now()}-2`,
            stepNumber: 2,
            roleRequired: 'FINANCE_OPERATIONS' as const,
            reviewerName: 'Elena Rostova',
            status: 'PENDING' as const,
            comment: 'Awaiting secondary Finance review for high blended risk score.'
          }
        );
      } else {
        steps.push({
          id: `step-${Date.now()}-1`,
          stepNumber: 1,
          roleRequired: 'SALES_MANAGER' as const,
          reviewerName: 'Marcus Vance',
          status: 'PENDING' as const,
          comment: 'Standard manager discount approval.'
        });
      }

      const newApproval: ApprovalInstance = {
        id: `app-${Date.now()}`,
        quotationId: recalculated.id,
        quoteNumber: recalculated.quoteNumber,
        customerName: recalculated.customerName,
        amount: recalculated.totalAmount,
        riskScore: recalculated.blendedRiskScore,
        status: 'PENDING',
        steps,
        submittedAt: new Date().toISOString(),
        reasons: recalculated.riskReasons,
        auditTimeline: [
          {
            id: `aud-${Date.now()}`,
            entityType: 'QUOTATION',
            entityId: recalculated.id,
            userName: currentUser.name,
            userRole: currentUser.role,
            action: 'SUBMITTED_FOR_APPROVAL',
            timestamp: new Date().toISOString(),
            reason: 'Automated approval routing triggered by backend governance.'
          }
        ]
      };

      setApprovals(prev => [newApproval, ...prev]);
      setQuotations(prev => prev.map(q => q.id === current.id ? { 
        ...recalculated, 
        stage: 'PENDING_APPROVAL',
        currentApprovalStep: 'MANAGER'
      } : q));

      showNotification(`Quotation ${recalculated.quoteNumber} routed to Approval Center (${recalculated.requiredApprovalLevel === 'MANAGER_AND_FINANCE' ? 'Manager → Finance' : 'Manager'})`, 'warning');
    } else {
      setQuotations(prev => prev.map(q => q.id === current.id ? { 
        ...recalculated, 
        stage: 'APPROVED',
        currentApprovalStep: 'COMPLETED'
      } : q));
      showNotification(`Quotation ${recalculated.quoteNumber} meets all discount ceilings. Auto-approved!`, 'success');
    }
  };

  const confirmActiveQuote = () => {
    setQuotations(prev => prev.map(q => q.id === selectedQuoteId ? { ...q, stage: 'CONFIRMED' } : q));
    showNotification(`Quotation ${activeQuotation.quoteNumber} confirmed and converted to active Order! Ready for fulfillment.`, 'success');
  };

  // Approvals Actions
  const approveCurrentStep = (approvalId: string, comment = 'Approved according to governance policy') => {
    setApprovals(prev => prev.map(app => {
      if (app.id !== approvalId) return app;

      const currentStepIdx = app.steps.findIndex(s => s.status === 'PENDING');
      if (currentStepIdx === -1) return app;

      const updatedSteps = [...app.steps];
      updatedSteps[currentStepIdx] = {
        ...updatedSteps[currentStepIdx],
        status: 'APPROVED',
        comment,
        decidedAt: new Date().toISOString()
      };

      const hasMoreSteps = currentStepIdx + 1 < updatedSteps.length;
      const finalStatus = hasMoreSteps ? 'PENDING' : 'APPROVED';

      const newAudit: AuditLog = {
        id: `aud-${Date.now()}`,
        entityType: 'APPROVAL',
        entityId: app.id,
        userName: currentUser.name,
        userRole: currentUser.title,
        action: 'APPROVED_STEP',
        timestamp: new Date().toISOString(),
        reason: comment,
        details: `Step ${currentStepIdx + 1} (${updatedSteps[currentStepIdx].roleRequired}) approved.`
      };

      if (!hasMoreSteps) {
        // Complete quotation approval
        setQuotations(qPrev => qPrev.map(q => q.id === app.quotationId ? {
          ...q,
          stage: 'APPROVED',
          currentApprovalStep: 'COMPLETED'
        } : q));
      }

      return {
        ...app,
        status: finalStatus,
        steps: updatedSteps,
        auditTimeline: [newAudit, ...app.auditTimeline]
      };
    }));

    showNotification(`Approval step recorded successfully.`, 'success');
  };

  const rejectApproval = (approvalId: string, reason: string) => {
    setApprovals(prev => prev.map(app => {
      if (app.id !== approvalId) return app;
      const updatedSteps = app.steps.map(s => s.status === 'PENDING' ? { ...s, status: 'REJECTED' as const, comment: reason, decidedAt: new Date().toISOString() } : s);
      
      setQuotations(qPrev => qPrev.map(q => q.id === app.quotationId ? {
        ...q,
        stage: 'REJECTED'
      } : q));

      return {
        ...app,
        status: 'REJECTED',
        steps: updatedSteps,
        auditTimeline: [
          {
            id: `aud-${Date.now()}`,
            entityType: 'APPROVAL',
            entityId: app.id,
            userName: currentUser.name,
            userRole: currentUser.title,
            action: 'REJECTED_QUOTATION',
            timestamp: new Date().toISOString(),
            reason
          },
          ...app.auditTimeline
        ]
      };
    }));
    showNotification(`Quotation rejected. Notice sent to sales representative.`, 'error');
  };

  const returnForRevision = (approvalId: string, reason: string) => {
    setApprovals(prev => prev.map(app => {
      if (app.id !== approvalId) return app;
      const updatedSteps = app.steps.map(s => s.status === 'PENDING' ? { ...s, status: 'REVISION_REQUESTED' as const, comment: reason, decidedAt: new Date().toISOString() } : s);
      
      setQuotations(qPrev => qPrev.map(q => q.id === app.quotationId ? {
        ...q,
        stage: 'RETURNED_FOR_REVISION'
      } : q));

      return {
        ...app,
        status: 'REVISION_REQUIRED',
        steps: updatedSteps,
        auditTimeline: [
          {
            id: `aud-${Date.now()}`,
            entityType: 'APPROVAL',
            entityId: app.id,
            userName: currentUser.name,
            userRole: currentUser.title,
            action: 'RETURNED_FOR_REVISION',
            timestamp: new Date().toISOString(),
            reason
          },
          ...app.auditTimeline
        ]
      };
    }));
    showNotification(`Returned quotation to rep for revision with reason logged.`, 'warning');
  };

  // Fulfillment Actions
  const acceptSuggestedSplit = (orderId: string) => {
    setFulfillments(prev => {
      const existing = prev[orderId];
      if (!existing) return prev;
      return {
        ...prev,
        [orderId]: {
          ...existing,
          status: 'ACCEPTED'
        }
      };
    });
    showNotification(`Recommended warehouse allocation accepted! Pick & pack manifests generated.`, 'success');
  };

  const overrideAllocation = (orderId: string, newAllocations: any[]) => {
    setFulfillments(prev => {
      const existing = prev[orderId];
      if (!existing) return prev;
      return {
        ...prev,
        [orderId]: {
          ...existing,
          status: 'MANUALLY_OVERRIDDEN',
          allocations: newAllocations
        }
      };
    });
    showNotification(`Warehouse allocation manually overridden and logged to audit trail.`, 'info');
  };

  const consolidateBackorder = (orderId: string) => {
    setFulfillments(prev => {
      const existing = prev[orderId];
      if (!existing) return prev;
      return {
        ...prev,
        [orderId]: {
          ...existing,
          backorderQuantity: 0,
          backorderProductNames: [],
          status: 'FULFILLED',
          consolidationAvailable: false
        }
      };
    });
    showNotification(`Backordered units consolidated from newly arrived stock. Order is now fully fulfilled!`, 'success');
  };

  // Billing Actions
  const recordPayment = (invoiceId: string, amount: number) => {
    setInvoices(prev => prev.map(inv => {
      if (inv.id !== invoiceId) return inv;
      const newPaid = inv.paidAmount + amount;
      const newStatus = newPaid >= inv.amount ? 'PAID' : 'PARTIALLY_PAID';
      return {
        ...inv,
        paidAmount: Math.min(inv.amount, newPaid),
        status: newStatus
      };
    }));
    showNotification(`Payment of $${amount.toLocaleString()} recorded. Invoice status updated!`, 'success');
  };

  const modifySubscription = (subId: string, deltaQty: number) => {
    setSubscriptions(prev => prev.map(sub => {
      if (sub.id !== subId) return sub;
      const newQty = Math.max(1, sub.quantity + deltaQty);
      const unitRate = sub.amount / sub.quantity;
      const newAmount = unitRate * newQty;
      const proration = deltaQty * (unitRate * 0.45); // Proration calculation
      return {
        ...sub,
        quantity: newQty,
        amount: newAmount,
        prorationApplied: Math.round(proration)
      };
    }));
    showNotification(`Subscription updated with mid-cycle proration adjustment.`, 'info');
  };

  // Customer Portal Negotiation
  const submitCustomerNegotiation = (quoteId: string, counterDiscount: number, notes: string) => {
    setQuotations(prev => prev.map(q => {
      if (q.id !== quoteId) return q;

      // Apply counter discount to the primary product line
      const updatedLines = q.lines.map((l, idx) => {
        if (idx === 0) {
          return { ...l, discountPercent: counterDiscount };
        }
        return l;
      });

      const recalculated = recalculateHelper({
        ...q,
        lines: updatedLines,
        stage: 'UNDER_NEGOTIATION'
      });

      // If customer requested discount pushes quotation beyond approval thresholds,
      // backend automatically re-enters approval workflow!
      if (recalculated.approvalRequired) {
        recalculated.stage = 'PENDING_APPROVAL';
        recalculated.currentApprovalStep = 'MANAGER';

        // create new approval instance for re-approval
        const newApp: ApprovalInstance = {
          id: `app-re-${Date.now()}`,
          quotationId: recalculated.id,
          quoteNumber: recalculated.quoteNumber,
          customerName: recalculated.customerName,
          amount: recalculated.totalAmount,
          riskScore: recalculated.blendedRiskScore,
          status: 'PENDING',
          steps: [
            {
              id: `step-re-1`,
              stepNumber: 1,
              roleRequired: 'SALES_MANAGER',
              reviewerName: 'Marcus Vance',
              status: 'PENDING',
              comment: `Re-approval required: Customer requested ${counterDiscount}% counter-discount.`
            }
          ],
          submittedAt: new Date().toISOString(),
          reasons: [`Customer portal counter-offer (${counterDiscount}%) exceeds standard tier ceiling.`],
          auditTimeline: [
            {
              id: `aud-neg-${Date.now()}`,
              entityType: 'NEGOTIATION',
              entityId: q.id,
              userName: 'David Kross (Customer)',
              userRole: 'Customer Portal User',
              action: 'SUBMITTED_COUNTER_PROPOSAL',
              timestamp: new Date().toISOString(),
              reason: notes
            }
          ]
        };
        setApprovals(aPrev => [newApp, ...aPrev]);
      }

      return recalculated;
    }));

    showNotification(`Counter-proposal submitted! The system recalculated risk and routed for re-approval if necessary.`, 'warning');
  };

  const customerConfirmQuote = (quoteId: string) => {
    setQuotations(prev => prev.map(q => q.id === quoteId ? { ...q, stage: 'CONFIRMED' } : q));
    showNotification(`Quotation confirmed by customer! Order generated and sent to warehouse fulfillment.`, 'success');
  };

  // Deal Health Actions
  const acknowledgeAlert = (alertId: string) => {
    setDealAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: 'ACKNOWLEDGED' } : a));
    showNotification(`Alert acknowledged. Logged to deal monitoring record.`, 'info');
  };

  const resolveAlert = (alertId: string) => {
    setDealAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: 'RESOLVED' } : a));
    showNotification(`Deal alert resolved successfully.`, 'success');
  };

  const triggerAlertNudge = (alertId: string) => {
    const alert = dealAlerts.find(a => a.id === alertId);
    showNotification(`Automated escalation nudge sent to ${alert?.ownerName || 'Sales Rep'} for Quotation ${alert?.quoteNumber}`, 'success');
  };

  return (
    <AppContext.Provider value={{
      currentUser,
      setCurrentUser,
      setUserRole,
      currentPage,
      setCurrentPage,
      selectedQuoteId,
      setSelectedQuoteId,
      quotations,
      activeQuotation,
      products,
      approvals,
      fulfillments,
      subscriptions,
      invoices,
      dealAlerts,
      recommendations,
      auditLogs,
      updateLineQuantity,
      updateLineDiscount,
      addProductToActiveQuote,
      removeLineFromQuote,
      addRecommendationToQuote,
      dismissRecommendation,
      recalculateActiveQuote,
      submitActiveQuoteForApproval,
      confirmActiveQuote,
      approveCurrentStep,
      rejectApproval,
      returnForRevision,
      acceptSuggestedSplit,
      overrideAllocation,
      consolidateBackorder,
      recordPayment,
      modifySubscription,
      submitCustomerNegotiation,
      customerConfirmQuote,
      acknowledgeAlert,
      resolveAlert,
      triggerAlertNudge,
      notification,
      showNotification,
      isGuideOpen,
      setIsGuideOpen
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
