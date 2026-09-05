import React, { createContext, useContext, useState, useEffect } from 'react';
import { 
  User, 
  UserRole, 
  Customer,
  Product, 
  Quotation, 
  QuotationLine, 
  ApprovalInstance, 
  ApprovalStep,
  ApprovalLevel,
  OrderFulfillment, 
  Invoice, 
  SubscriptionItem, 
  DealAlert, 
  Recommendation,
  AuditLog,
  NegotiationRequest,
  GovernanceConfig,
  AuthUserInfo
} from '../types';
import { authService } from '../services/authService';
import { 
  mockUsers, 
  mockCustomers,
  mockQuotations, 
  mockProducts, 
  mockApprovals, 
  mockFulfillments, 
  mockSubscriptions, 
  mockInvoices, 
  mockDealAlerts, 
  mockRecommendations,
  mockGovernanceConfig,
  mockNegotiations
} from '../mockData';

function loadFromStorage<T>(key: string, fallback: T): T {
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : fallback;
  } catch (e) {
    console.warn(`Error loading ${key} from localStorage:`, e);
    return fallback;
  }
}

function saveToStorage<T>(key: string, value: T): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (e) {
    console.warn(`Error saving ${key} to localStorage:`, e);
  }
}

interface AppContextType {
  currentUser: User;
  setCurrentUser: (user: User) => void;
  setUserRole: (role: UserRole) => void;
  currentPage: string;
  setCurrentPage: (page: string) => void;
  selectedQuoteId: string;
  setSelectedQuoteId: (id: string) => void;

  // Authentication State
  isAuthenticated: boolean;
  accessToken: string | null;
  setAuthSession: (token: string, user?: AuthUserInfo) => void;
  logout: () => Promise<void>;
  
  // Data
  customers: Customer[];
  quotations: Quotation[];
  activeQuotation: Quotation | undefined;
  products: Product[];
  approvals: ApprovalInstance[];
  fulfillments: Record<string, OrderFulfillment>;
  subscriptions: SubscriptionItem[];
  invoices: Invoice[];
  dealAlerts: DealAlert[];
  recommendations: Recommendation[];
  negotiations: NegotiationRequest[];
  auditLogs: AuditLog[];
  governanceConfig: GovernanceConfig;
  
  // Actions
  createNewQuotation: (customerId?: string) => string;
  updateLineQuantity: (lineId: string, delta: number) => void;
  updateLineDiscount: (lineId: string, discountPercent: number) => void;
  updateOrderDiscount: (quoteId: string, discountPercent: number) => void;
  updateActiveQuoteCustomer: (customerId: string) => void;
  addProductToActiveQuote: (productId: string) => void;
  removeLineFromQuote: (lineId: string) => void;
  addRecommendationToQuote: (recommendation: Recommendation) => void;
  dismissRecommendation: (productId: string) => void;
  recalculateActiveQuote: () => void;
  saveDraftQuote: () => void;
  sendQuoteToCustomer: () => void;
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
  issueCreditNote: (invoiceId: string, amount: number, reason: string) => void;
  modifySubscription: (subId: string, deltaQty: number) => void;
  
  // Portal Negotiation
  submitCustomerNegotiation: (
    quoteId: string, 
    counterDiscount: number, 
    notes: string, 
    lineComments?: { lineId: string; comment: string; productName?: string }[]
  ) => void;
  addLineComment: (quoteId: string, lineId: string, comment: string, authorName?: string) => void;
  respondToNegotiation: (
    quoteId: string, 
    action: 'ACCEPT' | 'COUNTER' | 'DECLINE', 
    counterDiscount?: number, 
    repNotes?: string
  ) => void;
  customerConfirmQuote: (quoteId: string) => void;
  
  // Health
  acknowledgeAlert: (alertId: string) => void;
  resolveAlert: (alertId: string) => void;
  triggerAlertNudge: (alertId: string) => void;
  
  // Governance Configuration
  updateGovernanceConfig: (newConfig: Partial<GovernanceConfig>) => void;
  resetDemoData: () => void;
  
  // Notifications
  notification: { message: string; type: 'success' | 'warning' | 'info' | 'error' } | null;
  showNotification: (message: string, type?: 'success' | 'warning' | 'info' | 'error') => void;
  
  // Quick test flow guide modal
  isGuideOpen: boolean;
  setIsGuideOpen: (open: boolean) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Authentication State
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => authService.isAuthenticated());
  const [accessToken, setAccessToken] = useState<string | null>(() => authService.getAccessToken());

  // Hydrated State with LocalStorage Persistence
  const [currentUser, setCurrentUser] = useState<User>(() => loadFromStorage('dealflow_user', mockUsers[0]));
  const [currentPage, setCurrentPage] = useState<string>(() => loadFromStorage('dealflow_page', 'login'));
  const [selectedQuoteId, setSelectedQuoteId] = useState<string>(() => loadFromStorage('dealflow_quote_id', 'q-1048'));

  // Attempt silent session restore on mount via HttpOnly cookie
  useEffect(() => {
    let isMounted = true;
    const restoreSession = async () => {
      try {
        const res = await authService.refresh();
        if (res.access_token && isMounted) {
          authService.setAccessToken(res.access_token);
          setAccessToken(res.access_token);
          setIsAuthenticated(true);
          const me = await authService.getMe();
          if (me && isMounted) {
            setCurrentUser(prev => ({
              ...prev,
              id: me.id || prev.id,
              name: me.name || prev.name,
              email: me.email || prev.email,
              role: (me.role as UserRole) || prev.role,
              customerId: (me.customer_id || me.customerId) ?? prev.customerId,
            }));
          }
        }
      } catch {
        if (isMounted) {
          setIsAuthenticated(false);
          setAccessToken(null);
        }
      }
    };

    restoreSession();
    return () => {
      isMounted = false;
    };
  }, []);
  
  const [customers] = useState<Customer[]>(mockCustomers);
  const [products] = useState<Product[]>(mockProducts);
  const [quotations, setQuotations] = useState<Quotation[]>(() => loadFromStorage('dealflow_quotations', mockQuotations));
  const [approvals, setApprovals] = useState<ApprovalInstance[]>(() => loadFromStorage('dealflow_approvals', mockApprovals));
  const [fulfillments, setFulfillments] = useState<Record<string, OrderFulfillment>>(() => loadFromStorage('dealflow_fulfillments', mockFulfillments));
  const [subscriptions, setSubscriptions] = useState<SubscriptionItem[]>(() => loadFromStorage('dealflow_subscriptions', mockSubscriptions));
  const [invoices, setInvoices] = useState<Invoice[]>(() => loadFromStorage('dealflow_invoices', mockInvoices));
  const [dealAlerts, setDealAlerts] = useState<DealAlert[]>(() => loadFromStorage('dealflow_alerts', mockDealAlerts));
  const [negotiations, setNegotiations] = useState<NegotiationRequest[]>(() => loadFromStorage('dealflow_negotiations', mockNegotiations));
  const [recommendations, setRecommendations] = useState<Recommendation[]>(mockRecommendations);
  const [governanceConfig, setGovernanceConfig] = useState<GovernanceConfig>(() => loadFromStorage('dealflow_governance_config', mockGovernanceConfig));
  
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>(() => loadFromStorage('dealflow_audit_logs', [
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
  ]));

  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'warning' | 'info' | 'error' } | null>(null);
  const [isGuideOpen, setIsGuideOpen] = useState<boolean>(false);

  // Sync to localStorage
  useEffect(() => { saveToStorage('dealflow_user', currentUser); }, [currentUser]);
  useEffect(() => { saveToStorage('dealflow_page', currentPage); }, [currentPage]);
  useEffect(() => { saveToStorage('dealflow_quote_id', selectedQuoteId); }, [selectedQuoteId]);
  useEffect(() => { saveToStorage('dealflow_quotations', quotations); }, [quotations]);
  useEffect(() => { saveToStorage('dealflow_approvals', approvals); }, [approvals]);
  useEffect(() => { saveToStorage('dealflow_fulfillments', fulfillments); }, [fulfillments]);
  useEffect(() => { saveToStorage('dealflow_subscriptions', subscriptions); }, [subscriptions]);
  useEffect(() => { saveToStorage('dealflow_invoices', invoices); }, [invoices]);
  useEffect(() => { saveToStorage('dealflow_alerts', dealAlerts); }, [dealAlerts]);
  useEffect(() => { saveToStorage('dealflow_negotiations', negotiations); }, [negotiations]);
  useEffect(() => { saveToStorage('dealflow_audit_logs', auditLogs); }, [auditLogs]);
  useEffect(() => { saveToStorage('dealflow_governance_config', governanceConfig); }, [governanceConfig]);

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

  const setAuthSession = (token: string, userInfo?: AuthUserInfo) => {
    authService.setAccessToken(token);
    setAccessToken(token);
    setIsAuthenticated(true);
    if (userInfo) {
      setCurrentUser(prev => ({
        ...prev,
        id: userInfo.id || prev.id,
        name: userInfo.name || userInfo.email.split('@')[0],
        email: userInfo.email,
        role: (userInfo.role as UserRole) || prev.role || 'SALES_REP',
        title: userInfo.title || prev.title,
        department: userInfo.department || prev.department,
        customerId: (userInfo.customer_id || userInfo.customerId) ?? prev.customerId
      }));
    }
  };

  const logout = async () => {
    await authService.logout();
    setAccessToken(null);
    setIsAuthenticated(false);
    setCurrentPage('login');
    showNotification('You have been signed out.', 'info');
  };

  const activeQuotation = quotations.find(q => q.id === selectedQuoteId) || quotations[0];

  // Authoritative recalculation according to configured governance rules
  const recalculateHelper = (quote: Quotation, config?: GovernanceConfig): Quotation => {
    const currentConfig = config || governanceConfig;
    let grossSubtotal = 0;
    let subtotalBeforeOrderDiscount = 0;
    let totalCost = 0;
    let lineDiscountsTotal = 0;
    let maxExcessPoints = 0;
    let sumExcessPoints = 0;
    const reasons: string[] = [];

    const tierCeiling = currentConfig.tierDiscountCeilings[quote.customerTier] ?? 10;

    const updatedLines = quote.lines.map(line => {
      const prod = products.find(p => p.id === line.productId);
      const unitPrice = line.unitPrice;
      const unitCost = line.unitCost;
      const qty = line.quantity;
      const disc = Math.max(0, Math.min(100, line.discountPercent));

      // Category ceiling from governance configuration
      const catCeiling = currentConfig.categoryDiscountCeilings[line.category] ?? (prod ? prod.categoryDiscountCeiling : 10);
      // Stricter (minimum) of customer tier ceiling and category ceiling wins
      const ceiling = Math.min(tierCeiling, catCeiling);
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

      grossSubtotal += grossLine;
      subtotalBeforeOrderDiscount += netLine;
      totalCost += costLine;
      lineDiscountsTotal += discAmount;

      return {
        ...line,
        allowedDiscountCeiling: ceiling,
        discountExcessPercent: Math.round(excess * 10) / 10,
        lineTotal: Math.round(netLine * 100) / 100,
        marginPercent: Math.round(lineMargin * 10) / 10
      };
    });

    // Order-level discount calculation (Bug B fix)
    const orderDiscountPercent = Math.max(0, Math.min(100, quote.orderDiscountPercent || 0));
    const orderDiscountAmount = subtotalBeforeOrderDiscount * (orderDiscountPercent / 100);
    const netSubtotal = Math.max(0, subtotalBeforeOrderDiscount - orderDiscountAmount);
    const totalDiscountAmount = lineDiscountsTotal + orderDiscountAmount;

    if (orderDiscountPercent > 0) {
      if (orderDiscountPercent > tierCeiling) {
        const orderExcess = orderDiscountPercent - tierCeiling;
        maxExcessPoints = Math.max(maxExcessPoints, orderExcess);
        sumExcessPoints += orderExcess;
        reasons.push(`Order discount (${orderDiscountPercent}%) exceeds ${quote.customerTier} tier limit (${tierCeiling}%) by +${orderExcess.toFixed(1)}%`);
      } else {
        reasons.push(`Order discount of ${orderDiscountPercent}% applied to net total.`);
      }
    }

    // Standard 8% estimated tax
    const taxAmount = Math.round(netSubtotal * 0.08 * 100) / 100;
    const totalAmount = Math.round((netSubtotal + taxAmount) * 100) / 100;
    const blendedMargin = netSubtotal > 0 ? ((netSubtotal - totalCost) / netSubtotal) * 100 : 0;

    // Blended risk score calculation (0 to 100)
    let riskScore = 15; // Base healthy score
    if (sumExcessPoints > 0) {
      riskScore += Math.round(maxExcessPoints * 3.5 + (sumExcessPoints - maxExcessPoints) * 2.0);
    }
    if (orderDiscountPercent > 0) {
      riskScore += Math.round(orderDiscountPercent * 2.5);
    }

    if (blendedMargin > 0 && blendedMargin < currentConfig.minCorporateMarginFloor) {
      riskScore += 22;
      reasons.push(`Blended margin (${blendedMargin.toFixed(1)}%) is below corporate safety floor (${currentConfig.minCorporateMarginFloor}%).`);
    } else if (blendedMargin > 0 && blendedMargin < currentConfig.minCorporateMarginFloor + 8) {
      riskScore += 10;
    }
    riskScore = Math.min(98, Math.max(10, riskScore));

    const managerThreshold = currentConfig.managerApprovalRiskThreshold;
    const financeThreshold = currentConfig.financeApprovalRiskThreshold;

    const riskStatus: 'HEALTHY' | 'MODERATE' | 'HIGH_RISK' = 
      riskScore >= financeThreshold ? 'HIGH_RISK' : riskScore >= managerThreshold ? 'MODERATE' : 'HEALTHY';
    
    const approvalRequired = riskScore >= managerThreshold;
    const requiredApprovalLevel: ApprovalLevel = 
      riskScore >= financeThreshold ? 'MANAGER_AND_FINANCE' : riskScore >= managerThreshold ? 'SALES_MANAGER' : 'NONE';

    if (riskScore >= financeThreshold) {
      reasons.push(`Blended risk (${riskScore}) exceeds Finance threshold (${financeThreshold}): requires sequential 2-tier approval (Manager → Finance).`);
    } else if (riskScore >= managerThreshold) {
      reasons.push(`Blended risk (${riskScore}) exceeds Manager threshold (${managerThreshold}): requires Sales Manager sign-off.`);
    } else {
      reasons.push('All parameters within standard limits. No approval required.');
    }

    return {
      ...quote,
      lines: updatedLines,
      orderDiscountPercent,
      subtotal: Math.round(netSubtotal * 100) / 100,
      totalDiscountAmount: Math.round(totalDiscountAmount * 100) / 100,
      taxAmount,
      totalAmount,
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

  // Create new Quotation (Bug C fix)
  const createNewQuotation = (customerId?: string): string => {
    let maxNumber = 1051;
    quotations.forEach(q => {
      const match = q.quoteNumber.match(/Q-(\d+)/);
      if (match) {
        const num = parseInt(match[1], 10);
        if (num > maxNumber) maxNumber = num;
      }
    });
    const nextNum = maxNumber + 1;
    const quoteNumber = `Q-${nextNum}`;
    const quoteId = `q-${nextNum}`;

    const targetCust = customers.find(c => c.id === customerId) || customers[0];

    const newQuote: Quotation = {
      id: quoteId,
      quoteNumber,
      customerId: targetCust.id,
      customerName: targetCust.name,
      customerTier: targetCust.tier,
      salesRepId: currentUser.id,
      salesRepName: currentUser.name || 'Sarah Chen',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      stage: 'DRAFT',
      lines: [],
      orderDiscountPercent: 0,
      subtotal: 0,
      totalDiscountAmount: 0,
      taxAmount: 0,
      totalAmount: 0,
      totalCost: 0,
      blendedMarginPercent: 0,
      blendedRiskScore: 10,
      riskStatus: 'HEALTHY',
      riskReasons: ['New draft quotation. Parameters initialized.'],
      approvalRequired: false,
      requiredApprovalLevel: 'NONE'
    };

    const newAudit: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'QUOTATION',
      entityId: quoteId,
      userName: currentUser.name,
      userRole: currentUser.title || currentUser.role,
      action: 'CREATED_QUOTATION',
      timestamp: new Date().toISOString(),
      details: `Created draft quotation ${quoteNumber} for ${targetCust.name}.`
    };

    setQuotations(prev => [newQuote, ...prev]);
    setAuditLogs(prev => [newAudit, ...prev]);
    setSelectedQuoteId(quoteId);
    setCurrentPage('quote-builder');
    showNotification(`Created draft quotation ${quoteNumber} for ${targetCust.name}`, 'success');
    return quoteId;
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
      return recalculateHelper({ ...q, lines: updatedLines });
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
      return recalculateHelper({ ...q, lines: updatedLines });
    }));
  };

  const updateOrderDiscount = (quoteId: string, discountPercent: number) => {
    setQuotations(prev => prev.map(q => {
      if (q.id !== quoteId) return q;
      const recalculated = recalculateHelper({
        ...q,
        orderDiscountPercent: Math.max(0, Math.min(100, discountPercent))
      });
      return recalculated;
    }));

    const auditEntry: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'QUOTATION',
      entityId: quoteId,
      userName: currentUser.name,
      userRole: currentUser.title || currentUser.role,
      action: 'UPDATED_ORDER_DISCOUNT',
      timestamp: new Date().toISOString(),
      details: `Order discount adjusted to ${discountPercent}%. Margin & governance risk recalculated.`
    };
    setAuditLogs(prev => [auditEntry, ...prev]);
  };

  const updateActiveQuoteCustomer = (customerId: string) => {
    const cust = customers.find(c => c.id === customerId);
    if (!cust) return;

    setQuotations(prev => prev.map(q => {
      if (q.id !== selectedQuoteId) return q;
      const updatedQuote = recalculateHelper({
        ...q,
        customerId: cust.id,
        customerName: cust.name,
        customerTier: cust.tier
      });
      return updatedQuote;
    }));

    showNotification(`Assigned quotation to ${cust.name} (${cust.tier} Tier)`, 'info');
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
      return recalculateHelper({ ...q, lines: updatedLines });
    }));

    const auditEntry: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'QUOTATION',
      entityId: selectedQuoteId,
      userName: currentUser.name,
      userRole: currentUser.title || currentUser.role,
      action: 'ADDED_PRODUCT_LINE',
      timestamp: new Date().toISOString(),
      details: `Added ${prod.name} (${prod.category}) at $${prod.unitPrice}.`
    };
    setAuditLogs(prev => [auditEntry, ...prev]);

    showNotification(`Added ${prod.name} to Quotation ${activeQuotation.quoteNumber}`, 'success');
  };

  const removeLineFromQuote = (lineId: string) => {
    const quote = activeQuotation;
    const removedLine = quote?.lines.find(l => l.id === lineId);

    setQuotations(prev => prev.map(q => {
      if (q.id !== selectedQuoteId) return q;
      const updatedLines = q.lines.filter(l => l.id !== lineId);
      return recalculateHelper({ ...q, lines: updatedLines });
    }));

    if (removedLine) {
      const auditEntry: AuditLog = {
        id: `aud-${Date.now()}`,
        entityType: 'QUOTATION',
        entityId: selectedQuoteId,
        userName: currentUser.name,
        userRole: currentUser.title || currentUser.role,
        action: 'REMOVED_PRODUCT_LINE',
        timestamp: new Date().toISOString(),
        details: `Removed line: ${removedLine.productName}.`
      };
      setAuditLogs(prev => [auditEntry, ...prev]);
    }

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
    showNotification(`Deal terms and margin recalculated with mock governance engine`, 'info');
  };

  const saveDraftQuote = () => {
    setQuotations(prev => prev.map(q => {
      if (q.id !== selectedQuoteId) return q;
      return {
        ...q,
        updatedAt: new Date().toISOString()
      };
    }));

    const auditEntry: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'QUOTATION',
      entityId: selectedQuoteId,
      userName: currentUser.name,
      userRole: currentUser.title || currentUser.role,
      action: 'SAVED_DRAFT',
      timestamp: new Date().toISOString(),
      details: 'Draft state saved to mock database store.'
    };
    setAuditLogs(prev => [auditEntry, ...prev]);

    showNotification(`Draft for ${activeQuotation.quoteNumber} saved successfully.`, 'success');
  };

  const sendQuoteToCustomer = () => {
    setQuotations(prev => prev.map(q => {
      if (q.id !== selectedQuoteId) return q;
      return {
        ...q,
        stage: 'SENT',
        updatedAt: new Date().toISOString()
      };
    }));

    const auditEntry: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'QUOTATION',
      entityId: selectedQuoteId,
      userName: currentUser.name,
      userRole: currentUser.title || currentUser.role,
      action: 'SENT_TO_CUSTOMER',
      timestamp: new Date().toISOString(),
      details: `Dispatched quotation proposal ${activeQuotation.quoteNumber} to customer portal.`
    };
    setAuditLogs(prev => [auditEntry, ...prev]);

    showNotification(`Sent Quotation ${activeQuotation.quoteNumber} to customer portal!`, 'success');
  };

  // Submit active quote for approval with sequential step routing
  const submitActiveQuoteForApproval = () => {
    const current = activeQuotation;
    const recalculated = recalculateHelper(current);

    if (recalculated.approvalRequired) {
      const steps: ApprovalStep[] = [];
      if (recalculated.requiredApprovalLevel === 'MANAGER_AND_FINANCE') {
        steps.push(
          {
            id: `step-${Date.now()}-1`,
            stepNumber: 1,
            roleRequired: 'SALES_MANAGER',
            reviewerName: 'Marcus Vance',
            status: 'PENDING',
            comment: 'Awaiting Manager review for discount ceiling violation.'
          },
          {
            id: `step-${Date.now()}-2`,
            stepNumber: 2,
            roleRequired: 'FINANCE_OPERATIONS',
            reviewerName: 'Elena Rostova',
            status: 'PENDING',
            comment: `Awaiting secondary Finance review because risk score (${recalculated.blendedRiskScore}) exceeds threshold.`
          }
        );
      } else {
        steps.push({
          id: `step-${Date.now()}-1`,
          stepNumber: 1,
          roleRequired: 'SALES_MANAGER',
          reviewerName: 'Marcus Vance',
          status: 'PENDING',
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
            userRole: currentUser.title || currentUser.role,
            action: 'SUBMITTED_FOR_APPROVAL',
            timestamp: new Date().toISOString(),
            reason: 'Automated approval routing triggered by mock governance engine.'
          }
        ]
      };

      setApprovals(prev => [newApproval, ...prev]);
      setQuotations(prev => prev.map(q => q.id === current.id ? { 
        ...recalculated, 
        stage: 'PENDING_APPROVAL',
        currentApprovalStep: 'MANAGER'
      } : q));

      const auditEntry: AuditLog = {
        id: `aud-${Date.now()}`,
        entityType: 'APPROVAL',
        entityId: newApproval.id,
        userName: currentUser.name,
        userRole: currentUser.title || currentUser.role,
        action: 'SUBMITTED_FOR_APPROVAL',
        timestamp: new Date().toISOString(),
        details: `Quotation routed to ${recalculated.requiredApprovalLevel === 'MANAGER_AND_FINANCE' ? 'Manager → Finance (2 tiers)' : 'Sales Manager (Tier 1)'}.`
      };
      setAuditLogs(prev => [auditEntry, ...prev]);

      showNotification(`Quotation ${recalculated.quoteNumber} routed to Approval Center (${recalculated.requiredApprovalLevel === 'MANAGER_AND_FINANCE' ? 'Manager → Finance' : 'Manager'})`, 'warning');
    } else {
      setQuotations(prev => prev.map(q => q.id === current.id ? { 
        ...recalculated, 
        stage: 'APPROVED',
        currentApprovalStep: 'COMPLETED'
      } : q));

      const auditEntry: AuditLog = {
        id: `aud-${Date.now()}`,
        entityType: 'QUOTATION',
        entityId: recalculated.id,
        userName: 'Governance Engine',
        userRole: 'Automated Evaluator',
        action: 'AUTO_APPROVED',
        timestamp: new Date().toISOString(),
        details: 'All commercial parameters within standard discount ceilings. Approval bypassed.'
      };
      setAuditLogs(prev => [auditEntry, ...prev]);

      showNotification(`Quotation ${recalculated.quoteNumber} meets all discount ceilings. Auto-approved!`, 'success');
    }
  };

  const confirmActiveQuote = () => {
    const q = activeQuotation;
    setQuotations(prev => prev.map(item => item.id === selectedQuoteId ? { ...item, stage: 'CONFIRMED' } : item));

    // Ensure a fulfillment entry exists for this confirmed quote
    const orderKey = `ord-${q.quoteNumber.replace('Q-', '')}`;
    if (!fulfillments[orderKey]) {
      const newFulfillment: OrderFulfillment = {
        orderId: orderKey,
        quotationId: q.id,
        quoteNumber: q.quoteNumber,
        customerName: q.customerName,
        status: 'SUGGESTED',
        allocations: q.lines.filter(l => !l.isSubscription).map(l => ({
          warehouseId: 'wh-1',
          warehouseName: 'Main Distribution Center (Chicago)',
          productId: l.productId,
          productName: l.productName,
          quantityAllocated: l.quantity,
          estimatedShipments: 1,
          estimatedCost: 350
        })),
        totalShipments: 1,
        totalShippingCost: 350,
        backorderQuantity: 0,
        backorderProductNames: [],
        consolidationAvailable: false
      };
      setFulfillments(prev => ({ ...prev, [orderKey]: newFulfillment }));
    }

    const auditEntry: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'QUOTATION',
      entityId: selectedQuoteId,
      userName: currentUser.name,
      userRole: currentUser.title || currentUser.role,
      action: 'CONFIRMED_DEAL',
      timestamp: new Date().toISOString(),
      details: `Commercial order confirmed. Converted to active fulfillment & billing streams.`
    };
    setAuditLogs(prev => [auditEntry, ...prev]);

    showNotification(`Quotation ${q.quoteNumber} confirmed and converted to active Order! Ready for fulfillment.`, 'success');
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
        reviewerName: currentUser.name,
        reviewerId: currentUser.id,
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
        userRole: currentUser.title || currentUser.role,
        action: 'APPROVED_STEP',
        timestamp: new Date().toISOString(),
        reason: comment,
        details: `Step ${currentStepIdx + 1} (${updatedSteps[currentStepIdx].roleRequired}) approved by ${currentUser.name}.`
      };

      if (!hasMoreSteps) {
        // Complete quotation approval
        setQuotations(qPrev => qPrev.map(q => q.id === app.quotationId ? {
          ...q,
          stage: 'APPROVED',
          currentApprovalStep: 'COMPLETED'
        } : q));
      } else {
        // Advance to next sequential role
        const nextRole = updatedSteps[currentStepIdx + 1].roleRequired;
        setQuotations(qPrev => qPrev.map(q => q.id === app.quotationId ? {
          ...q,
          currentApprovalStep: nextRole === 'FINANCE_OPERATIONS' ? 'FINANCE' : 'MANAGER'
        } : q));
      }

      return {
        ...app,
        status: finalStatus,
        steps: updatedSteps,
        auditTimeline: [newAudit, ...app.auditTimeline]
      };
    }));

    const globalAudit: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'APPROVAL',
      entityId: approvalId,
      userName: currentUser.name,
      userRole: currentUser.title || currentUser.role,
      action: 'STEP_APPROVED',
      timestamp: new Date().toISOString(),
      reason: comment
    };
    setAuditLogs(prev => [globalAudit, ...prev]);

    showNotification(`Approval step recorded successfully.`, 'success');
  };

  const rejectApproval = (approvalId: string, reason: string) => {
    setApprovals(prev => prev.map(app => {
      if (app.id !== approvalId) return app;
      const updatedSteps = app.steps.map(s => s.status === 'PENDING' ? { 
        ...s, 
        status: 'REJECTED' as const, 
        reviewerName: currentUser.name,
        reviewerId: currentUser.id,
        comment: reason, 
        decidedAt: new Date().toISOString() 
      } : s);
      
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
            userRole: currentUser.title || currentUser.role,
            action: 'REJECTED_QUOTATION',
            timestamp: new Date().toISOString(),
            reason
          },
          ...app.auditTimeline
        ]
      };
    }));

    const globalAudit: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'APPROVAL',
      entityId: approvalId,
      userName: currentUser.name,
      userRole: currentUser.title || currentUser.role,
      action: 'REJECTED_QUOTATION',
      timestamp: new Date().toISOString(),
      reason
    };
    setAuditLogs(prev => [globalAudit, ...prev]);

    showNotification(`Quotation rejected. Notice sent to sales representative.`, 'error');
  };

  const returnForRevision = (approvalId: string, reason: string) => {
    setApprovals(prev => prev.map(app => {
      if (app.id !== approvalId) return app;
      const updatedSteps = app.steps.map(s => s.status === 'PENDING' ? { 
        ...s, 
        status: 'REVISION_REQUESTED' as const, 
        reviewerName: currentUser.name,
        reviewerId: currentUser.id,
        comment: reason, 
        decidedAt: new Date().toISOString() 
      } : s);
      
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
            userRole: currentUser.title || currentUser.role,
            action: 'RETURNED_FOR_REVISION',
            timestamp: new Date().toISOString(),
            reason
          },
          ...app.auditTimeline
        ]
      };
    }));

    const globalAudit: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'APPROVAL',
      entityId: approvalId,
      userName: currentUser.name,
      userRole: currentUser.title || currentUser.role,
      action: 'RETURNED_FOR_REVISION',
      timestamp: new Date().toISOString(),
      reason
    };
    setAuditLogs(prev => [globalAudit, ...prev]);

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

    const auditEntry: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'FULFILLMENT',
      entityId: orderId,
      userName: currentUser.name,
      userRole: currentUser.title || currentUser.role,
      action: 'ACCEPTED_WAREHOUSE_SPLIT',
      timestamp: new Date().toISOString(),
      details: 'Operations accepted automated warehouse split recommendation.'
    };
    setAuditLogs(prev => [auditEntry, ...prev]);

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

    const auditEntry: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'FULFILLMENT',
      entityId: orderId,
      userName: currentUser.name,
      userRole: currentUser.title || currentUser.role,
      action: 'OVERRODE_WAREHOUSE_ALLOCATION',
      timestamp: new Date().toISOString(),
      details: 'Manual override committed to fulfillment allocation.'
    };
    setAuditLogs(prev => [auditEntry, ...prev]);

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

    const auditEntry: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'FULFILLMENT',
      entityId: orderId,
      userName: currentUser.name,
      userRole: currentUser.title || currentUser.role,
      action: 'CONSOLIDATED_BACKORDER',
      timestamp: new Date().toISOString(),
      details: 'Consolidated backordered quantity from newly replenished stock. Order fully dispatched.'
    };
    setAuditLogs(prev => [auditEntry, ...prev]);

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

    const auditEntry: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'BILLING',
      entityId: invoiceId,
      userName: currentUser.name,
      userRole: currentUser.title || currentUser.role,
      action: 'RECORDED_PAYMENT',
      timestamp: new Date().toISOString(),
      details: `Recorded payment of $${amount.toLocaleString()} against invoice ${invoiceId}.`
    };
    setAuditLogs(prev => [auditEntry, ...prev]);

    showNotification(`Payment of $${amount.toLocaleString()} recorded. Invoice status updated!`, 'success');
  };

  const issueCreditNote = (invoiceId: string, amount: number, reason: string) => {
    const targetInv = invoices.find(i => i.id === invoiceId);
    if (!targetInv) return;

    const creditInv: Invoice = {
      id: `inv-cn-${Date.now()}`,
      invoiceNumber: `CN-2026-${Math.floor(1000 + Math.random() * 9000)}`,
      orderId: targetInv.orderId,
      customerName: targetInv.customerName,
      type: 'CREDIT_NOTE',
      amount: amount,
      paidAmount: amount,
      status: 'PAID',
      dueDate: new Date().toISOString().split('T')[0],
      issuedAt: new Date().toISOString().split('T')[0]
    };

    setInvoices(prev => [creditInv, ...prev.map(inv => {
      if (inv.id !== invoiceId) return inv;
      const newPaid = Math.min(inv.amount, inv.paidAmount + amount);
      return {
        ...inv,
        paidAmount: newPaid,
        status: newPaid >= inv.amount ? 'PAID' : 'PARTIALLY_PAID'
      };
    })]);

    const auditEntry: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'BILLING',
      entityId: invoiceId,
      userName: currentUser.name,
      userRole: currentUser.title || currentUser.role,
      action: 'ISSUED_CREDIT_NOTE',
      timestamp: new Date().toISOString(),
      reason,
      details: `Credit note ${creditInv.invoiceNumber} of $${amount.toLocaleString()} issued against ${targetInv.invoiceNumber}.`
    };
    setAuditLogs(prev => [auditEntry, ...prev]);

    showNotification(`Credit note ${creditInv.invoiceNumber} ($${amount.toLocaleString()}) issued & reconciled!`, 'success');
  };

  const modifySubscription = (subId: string, deltaQty: number) => {
    setSubscriptions(prev => prev.map(sub => {
      if (sub.id !== subId) return sub;
      const newQty = Math.max(1, sub.quantity + deltaQty);
      const unitRate = sub.amount / sub.quantity;
      const newAmount = unitRate * newQty;
      const proration = deltaQty * (unitRate * 0.45);
      return {
        ...sub,
        quantity: newQty,
        amount: newAmount,
        prorationApplied: Math.round(proration)
      };
    }));

    const auditEntry: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'BILLING',
      entityId: subId,
      userName: currentUser.name,
      userRole: currentUser.title || currentUser.role,
      action: 'MODIFIED_SUBSCRIPTION',
      timestamp: new Date().toISOString(),
      details: `Subscription adjusted by ${deltaQty > 0 ? '+' : ''}${deltaQty} unit(s) with mid-cycle proration.`
    };
    setAuditLogs(prev => [auditEntry, ...prev]);

    showNotification(`Subscription updated with mid-cycle proration adjustment.`, 'info');
  };

  // Customer Portal Line Comments (Bug Q fix)
  const addLineComment = (quoteId: string, lineId: string, comment: string, authorName?: string) => {
    setQuotations(prev => prev.map(q => {
      if (q.id !== quoteId) return q;
      const updatedLines = q.lines.map(line => {
        if (line.id === lineId) {
          const prevComments = line.comments || [];
          return {
            ...line,
            comments: [...prevComments, `${authorName || currentUser.name}: ${comment}`]
          };
        }
        return line;
      });
      return { ...q, lines: updatedLines, updatedAt: new Date().toISOString() };
    }));

    showNotification(`Comment added to line item.`, 'info');
  };

  // Customer Portal Negotiation with Automatic Sequential Re-Approval (Bug H fix)
  const submitCustomerNegotiation = (
    quoteId: string, 
    counterDiscount: number, 
    notes: string,
    lineComments?: { lineId: string; comment: string; productName?: string }[]
  ) => {
    let createdApp: ApprovalInstance | null = null;

    setQuotations(prev => prev.map(q => {
      if (q.id !== quoteId) return q;

      // Apply counter discount to primary line
      const updatedLines = q.lines.map((l, idx) => {
        if (idx === 0) {
          return { ...l, discountPercent: counterDiscount };
        }
        return l;
      });

      const recalculated = recalculateHelper({
        ...q,
        lines: updatedLines,
        stage: 'UNDER_NEGOTIATION',
        hasActiveNegotiation: true
      });

      // If counter-proposal breaches approval thresholds, auto-route
      if (recalculated.approvalRequired) {
        recalculated.stage = 'PENDING_APPROVAL';
        recalculated.currentApprovalStep = 'MANAGER';

        const steps: ApprovalStep[] = [];
        // Sequential 2-tier approval if high risk!
        if (recalculated.requiredApprovalLevel === 'MANAGER_AND_FINANCE') {
          steps.push(
            {
              id: `step-re-${Date.now()}-1`,
              stepNumber: 1,
              roleRequired: 'SALES_MANAGER',
              reviewerName: 'Marcus Vance',
              status: 'PENDING',
              comment: `Customer counter-offer: requested ${counterDiscount}% discount.`
            },
            {
              id: `step-re-${Date.now()}-2`,
              stepNumber: 2,
              roleRequired: 'FINANCE_OPERATIONS',
              reviewerName: 'Elena Rostova',
              status: 'PENDING',
              comment: `Tier 2 Finance review required: negotiated risk (${recalculated.blendedRiskScore}) exceeds threshold.`
            }
          );
        } else {
          steps.push({
            id: `step-re-${Date.now()}-1`,
            stepNumber: 1,
            roleRequired: 'SALES_MANAGER',
            reviewerName: 'Marcus Vance',
            status: 'PENDING',
            comment: `Customer counter-offer: requested ${counterDiscount}% discount.`
          });
        }

        createdApp = {
          id: `app-re-${Date.now()}`,
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
              id: `aud-neg-${Date.now()}`,
              entityType: 'NEGOTIATION',
              entityId: q.id,
              userName: currentUser.name || 'David Kross (Customer)',
              userRole: 'Customer Portal',
              action: 'SUBMITTED_COUNTER_PROPOSAL',
              timestamp: new Date().toISOString(),
              reason: notes,
              details: `Customer requested ${counterDiscount}% discount. Triggered automatic re-approval.`
            }
          ]
        };
      }

      return recalculated;
    }));

    if (createdApp) {
      setApprovals(aPrev => [createdApp!, ...aPrev]);
    }

    const newNeg: NegotiationRequest = {
      id: `neg-${Date.now()}`,
      quotationId: quoteId,
      customerName: activeQuotation?.customerName || 'Customer Account',
      requestedDiscountPercent: counterDiscount,
      notes,
      status: 'PENDING_REVIEW',
      createdAt: new Date().toISOString(),
      lineComments: lineComments || []
    };
    setNegotiations(prev => [newNeg, ...prev.filter(n => n.quotationId !== quoteId)]);

    const auditEntry: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'NEGOTIATION',
      entityId: quoteId,
      userName: currentUser.name,
      userRole: 'Customer Portal',
      action: 'SUBMITTED_COUNTER_PROPOSAL',
      timestamp: new Date().toISOString(),
      reason: notes,
      details: `Customer proposed ${counterDiscount}% discount.`
    };
    setAuditLogs(prev => [auditEntry, ...prev]);

    showNotification(`Counter-proposal submitted! The system recalculated risk and routed for re-approval if necessary.`, 'warning');
  };

  // Sales Rep Negotiation Response Workflow (Bug F fix)
  const respondToNegotiation = (
    quoteId: string, 
    action: 'ACCEPT' | 'COUNTER' | 'DECLINE', 
    counterDiscount?: number, 
    repNotes?: string
  ) => {
    const quote = quotations.find(q => q.id === quoteId);
    if (!quote) return;

    const updatedNegStatus = action === 'ACCEPT' ? 'ACCEPTED' : action === 'COUNTER' ? 'COUNTERED' : 'REJECTED';

    setNegotiations(prev => prev.map(n => {
      if (n.quotationId !== quoteId) return n;
      return {
        ...n,
        status: updatedNegStatus,
        repResponseNotes: repNotes,
        counterDiscountPercent: counterDiscount,
        respondedAt: new Date().toISOString()
      };
    }));

    if (action === 'ACCEPT') {
      setQuotations(prev => prev.map(q => {
        if (q.id !== quoteId) return q;
        const recalculated = recalculateHelper({
          ...q,
          hasActiveNegotiation: false,
          stage: q.approvalRequired ? 'PENDING_APPROVAL' : 'APPROVED'
        });
        return recalculated;
      }));
      showNotification(`Accepted customer terms for ${quote.quoteNumber}.`, 'success');
    } else if (action === 'COUNTER') {
      const newDisc = counterDiscount ?? 10;
      setQuotations(prev => prev.map(q => {
        if (q.id !== quoteId) return q;
        const updatedLines = q.lines.map((l, idx) => idx === 0 ? { ...l, discountPercent: newDisc } : l);
        const recalculated = recalculateHelper({
          ...q,
          lines: updatedLines,
          hasActiveNegotiation: false,
          stage: 'SENT'
        });
        return recalculated;
      }));
      showNotification(`Sent counter-proposal (${counterDiscount}%) to customer for ${quote.quoteNumber}.`, 'info');
    } else {
      setQuotations(prev => prev.map(q => {
        if (q.id !== quoteId) return q;
        return {
          ...q,
          hasActiveNegotiation: false,
          stage: 'SENT'
        };
      }));
      showNotification(`Declined negotiation for ${quote.quoteNumber}. Original terms maintained.`, 'info');
    }

    const auditEntry: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'NEGOTIATION',
      entityId: quoteId,
      userName: currentUser.name,
      userRole: currentUser.title || currentUser.role,
      action: `REP_${action}_NEGOTIATION`,
      timestamp: new Date().toISOString(),
      reason: repNotes,
      details: `Representative responded with ${action}. Counter: ${counterDiscount !== undefined ? `${counterDiscount}%` : 'N/A'}.`
    };
    setAuditLogs(prev => [auditEntry, ...prev]);
  };

  const customerConfirmQuote = (quoteId: string) => {
    setQuotations(prev => prev.map(q => q.id === quoteId ? { ...q, stage: 'CONFIRMED' } : q));

    // Ensure a fulfillment entry exists
    const q = quotations.find(item => item.id === quoteId);
    if (q) {
      const orderKey = `ord-${q.quoteNumber.replace('Q-', '')}`;
      if (!fulfillments[orderKey]) {
        const newFulfillment: OrderFulfillment = {
          orderId: orderKey,
          quotationId: q.id,
          quoteNumber: q.quoteNumber,
          customerName: q.customerName,
          status: 'SUGGESTED',
          allocations: q.lines.filter(l => !l.isSubscription).map(l => ({
            warehouseId: 'wh-1',
            warehouseName: 'Main Distribution Center (Chicago)',
            productId: l.productId,
            productName: l.productName,
            quantityAllocated: l.quantity,
            estimatedShipments: 1,
            estimatedCost: 350
          })),
          totalShipments: 1,
          totalShippingCost: 350,
          backorderQuantity: 0,
          backorderProductNames: [],
          consolidationAvailable: false
        };
        setFulfillments(prev => ({ ...prev, [orderKey]: newFulfillment }));
      }
    }

    const auditEntry: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'QUOTATION',
      entityId: quoteId,
      userName: currentUser.name,
      userRole: 'Customer Portal',
      action: 'CUSTOMER_CONFIRMED_DEAL',
      timestamp: new Date().toISOString(),
      details: 'Customer accepted and confirmed commercial deliverables online.'
    };
    setAuditLogs(prev => [auditEntry, ...prev]);

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

  // Governance Configuration
  const updateGovernanceConfig = (newConfig: Partial<GovernanceConfig>) => {
    const updated: GovernanceConfig = {
      ...governanceConfig,
      ...newConfig
    };
    setGovernanceConfig(updated);

    // Re-evaluate active quotation under new governance
    setQuotations(prev => prev.map(q => {
      if (q.id !== selectedQuoteId) return q;
      return recalculateHelper(q, updated);
    }));

    const auditEntry: AuditLog = {
      id: `aud-${Date.now()}`,
      entityType: 'APPROVAL',
      entityId: 'gov-config',
      userName: currentUser.name,
      userRole: currentUser.title || currentUser.role,
      action: 'UPDATED_GOVERNANCE_POLICY',
      timestamp: new Date().toISOString(),
      details: 'Updated discount ceilings, margin thresholds, or approval policies.'
    };
    setAuditLogs(prev => [auditEntry, ...prev]);

    showNotification('Governance policies committed & active quote re-evaluated.', 'success');
  };

  const resetDemoData = () => {
    try {
      localStorage.clear();
    } catch (e) {
      console.warn(e);
    }
    setCurrentUser(mockUsers[0]);
    setCurrentPage('dashboard');
    setSelectedQuoteId('q-1048');
    setQuotations(mockQuotations);
    setApprovals(mockApprovals);
    setFulfillments(mockFulfillments);
    setSubscriptions(mockSubscriptions);
    setInvoices(mockInvoices);
    setDealAlerts(mockDealAlerts);
    setNegotiations(mockNegotiations);
    setGovernanceConfig(mockGovernanceConfig);
    setRecommendations(mockRecommendations);
    setAuditLogs([
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
    showNotification('Demo seed data reset to pristine initial state.', 'info');
  };

  return (
    <AppContext.Provider value={{
      isAuthenticated,
      accessToken,
      setAuthSession,
      logout,
      currentUser,
      setCurrentUser,
      setUserRole,
      currentPage,
      setCurrentPage,
      selectedQuoteId,
      setSelectedQuoteId,
      customers,
      quotations,
      activeQuotation,
      products,
      approvals,
      fulfillments,
      subscriptions,
      invoices,
      dealAlerts,
      recommendations,
      negotiations,
      auditLogs,
      governanceConfig,
      createNewQuotation,
      updateLineQuantity,
      updateLineDiscount,
      updateOrderDiscount,
      updateActiveQuoteCustomer,
      addProductToActiveQuote,
      removeLineFromQuote,
      addRecommendationToQuote,
      dismissRecommendation,
      recalculateActiveQuote,
      saveDraftQuote,
      sendQuoteToCustomer,
      submitActiveQuoteForApproval,
      confirmActiveQuote,
      approveCurrentStep,
      rejectApproval,
      returnForRevision,
      acceptSuggestedSplit,
      overrideAllocation,
      consolidateBackorder,
      recordPayment,
      issueCreditNote,
      modifySubscription,
      submitCustomerNegotiation,
      addLineComment,
      respondToNegotiation,
      customerConfirmQuote,
      acknowledgeAlert,
      resolveAlert,
      triggerAlertNudge,
      updateGovernanceConfig,
      resetDemoData,
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
