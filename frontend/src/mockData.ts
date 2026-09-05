import { 
  Customer, 
  Product, 
  Quotation, 
  ApprovalInstance, 
  Warehouse, 
  OrderFulfillment, 
  Invoice, 
  DealAlert, 
  Recommendation, 
  User,
  SubscriptionItem,
  NegotiationRequest,
  GovernanceConfig
} from './types';

export const mockUsers: User[] = [
  {
    id: 'usr-1',
    name: 'Sarah Chen',
    email: 'sarah.chen@dealflow360.io',
    role: 'SALES_REP',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&auto=format&fit=crop&q=80',
    title: 'Senior Enterprise Account Executive',
    department: 'Direct Sales'
  },
  {
    id: 'usr-2',
    name: 'Marcus Vance',
    email: 'marcus.vance@dealflow360.io',
    role: 'SALES_MANAGER',
    avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&auto=format&fit=crop&q=80',
    title: 'VP of Commercial Sales & Governance',
    department: 'Sales Management'
  },
  {
    id: 'usr-3',
    name: 'Elena Rostova',
    email: 'elena.rostova@dealflow360.io',
    role: 'FINANCE_OPERATIONS',
    avatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80',
    title: 'Director of Revenue Operations & Finance',
    department: 'Finance & Supply Chain'
  },
  {
    id: 'usr-4',
    name: 'David Kross',
    email: 'david.kross@acmecorp.com',
    role: 'CUSTOMER_PORTAL',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
    title: 'VP Procurement & Infrastructure',
    department: 'Acme Corporation',
    customerId: 'cust-1'
  },
  {
    id: 'usr-5',
    name: 'Alex Mercer',
    email: 'admin@dealflow360.io',
    role: 'ADMIN',
    avatar: 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150&auto=format&fit=crop&q=80',
    title: 'Platform Administrator & Architect',
    department: 'RevOps Operations'
  },
  {
    id: 'usr-6',
    name: 'Carlos Ruiz',
    email: 'carlos.ruiz@dealflow360.io',
    role: 'FULFILLMENT_OPERATOR',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80',
    title: 'Logistics & Warehouse Operations Lead',
    department: 'Supply Chain & Logistics'
  }
];

export const mockCustomers: Customer[] = [
  {
    id: 'cust-1',
    name: 'Acme Corporation',
    companyNumber: 'ACM-9021',
    tier: 'GOLD',
    industry: 'Enterprise Software & Cloud',
    contactName: 'David Kross',
    contactEmail: 'david.kross@acmecorp.com',
    defaultDiscountCeiling: 15,
    balance: 145200
  },
  {
    id: 'cust-2',
    name: 'NovaTech Industries',
    companyNumber: 'NOV-4412',
    tier: 'SILVER',
    industry: 'Advanced Robotics & Automation',
    contactName: 'Rachel Green',
    contactEmail: 'rachel.g@novatech.com',
    defaultDiscountCeiling: 10,
    balance: 82500
  },
  {
    id: 'cust-3',
    name: 'Vertex Systems',
    companyNumber: 'VTX-7731',
    tier: 'BRONZE',
    industry: 'Logistics Telematics',
    contactName: 'James Wilson',
    contactEmail: 'j.wilson@vertexsys.com',
    defaultDiscountCeiling: 5,
    balance: 34000
  },
  {
    id: 'cust-4',
    name: 'Orion Manufacturing',
    companyNumber: 'ORN-1109',
    tier: 'PLATINUM',
    industry: 'Industrial Aerospace',
    contactName: 'Catherine Dupont',
    contactEmail: 'c.dupont@orionmfg.com',
    defaultDiscountCeiling: 20,
    balance: 320000
  }
];

export const mockProducts: Product[] = [
  {
    id: 'prod-1',
    name: 'Enterprise Edge Server X4',
    sku: 'HW-SRV-X4',
    category: 'HARDWARE',
    unitPrice: 4800,
    unitCost: 2600,
    unit: 'Unit',
    taxRate: 0.08,
    description: 'High-density 2U rackmount compute server with dual Xeon Gold processors.',
    isSubscriptionEligible: false,
    categoryDiscountCeiling: 15
  },
  {
    id: 'prod-2',
    name: 'Network Security Appliance Pro',
    sku: 'HW-NET-SEC',
    category: 'HARDWARE',
    unitPrice: 3400,
    unitCost: 1900,
    unit: 'Unit',
    taxRate: 0.08,
    description: 'Unified threat management gateway with multi-gigabit throughput and DPI.',
    isSubscriptionEligible: false,
    categoryDiscountCeiling: 12
  },
  {
    id: 'prod-3',
    name: 'Cloud Backup & Disaster Recovery',
    sku: 'SUB-CLD-BKUP',
    category: 'SUBSCRIPTION',
    unitPrice: 450,
    unitCost: 90,
    unit: 'Node/mo',
    taxRate: 0.05,
    description: 'Continuous immutable cloud replication with 15-minute RTO SLA.',
    isSubscriptionEligible: true,
    recurringInterval: 'MONTHLY',
    categoryDiscountCeiling: 15
  },
  {
    id: 'prod-4',
    name: 'Premium 24/7 Dedicated Support',
    sku: 'SVC-SUP-PREM',
    category: 'SERVICES',
    unitPrice: 1200,
    unitCost: 800,
    unit: 'Mo',
    taxRate: 0.0,
    description: 'Named Technical Account Manager with guaranteed 30-minute response escalation.',
    isSubscriptionEligible: true,
    recurringInterval: 'MONTHLY',
    categoryDiscountCeiling: 10
  },
  {
    id: 'prod-5',
    name: 'Custom Implementation & Migration',
    sku: 'SVC-IMPL-PKG',
    category: 'SERVICES',
    unitPrice: 3500,
    unitCost: 2400,
    unit: 'Engagement',
    taxRate: 0.0,
    description: 'Hands-on architectural setup, data migration, and onsite operational training.',
    isSubscriptionEligible: false,
    categoryDiscountCeiling: 8
  },
  {
    id: 'prod-6',
    name: 'AI Inference Acceleration Module',
    sku: 'HW-AI-ACC',
    category: 'HARDWARE',
    unitPrice: 7500,
    unitCost: 4500,
    unit: 'Module',
    taxRate: 0.08,
    description: 'Tensor acceleration coprocessor for edge machine learning workloads.',
    isSubscriptionEligible: false,
    categoryDiscountCeiling: 10
  }
];

export const mockRecommendations: Recommendation[] = [
  {
    productId: 'prod-4',
    productName: 'Premium 24/7 Dedicated Support',
    category: 'SERVICES',
    unitPrice: 1200,
    marginDelta: 4.2,
    promotionTag: 'High Margin Add-on',
    reason: 'Customers purchasing Enterprise Servers consistently attach 24/7 Support. Boosts blended deal margin by 4.2%.'
  },
  {
    productId: 'prod-3',
    productName: 'Cloud Backup & Disaster Recovery',
    category: 'SUBSCRIPTION',
    unitPrice: 450,
    marginDelta: 6.8,
    promotionTag: 'Recurring Bundling',
    reason: 'Recurring cloud backup boasts an 80% gross margin and stabilizes multi-year account lifetime value.'
  },
  {
    productId: 'prod-2',
    productName: 'Network Security Appliance Pro',
    category: 'HARDWARE',
    unitPrice: 3400,
    marginDelta: 2.1,
    promotionTag: 'Security Defense Co-sell',
    reason: 'Co-purchase history indicates 64% of compute cluster deployments bundle perimeter hardware security.'
  }
];

export const mockQuotations: Quotation[] = [
  {
    id: 'q-1048',
    quoteNumber: 'Q-1048',
    customerId: 'cust-1',
    customerName: 'Acme Corporation',
    customerTier: 'GOLD',
    salesRepId: 'usr-1',
    salesRepName: 'Sarah Chen',
    createdAt: '2026-09-02T10:30:00Z',
    updatedAt: '2026-09-04T16:45:00Z',
    stage: 'PENDING_APPROVAL',
    lines: [
      {
        id: 'ql-1',
        productId: 'prod-1',
        productName: 'Enterprise Edge Server X4',
        category: 'HARDWARE',
        quantity: 6,
        unitPrice: 4800,
        unitCost: 2600,
        discountPercent: 12,
        allowedDiscountCeiling: 15,
        discountExcessPercent: 0,
        lineTotal: 25344, // 6 * 4800 * (1 - 0.12)
        marginPercent: 38.4,
        isSubscription: false
      },
      {
        id: 'ql-2',
        productId: 'prod-5',
        productName: 'Custom Implementation & Migration',
        category: 'SERVICES',
        quantity: 1,
        unitPrice: 3500,
        unitCost: 2400,
        discountPercent: 18, // Over ceiling of 8%!
        allowedDiscountCeiling: 8,
        discountExcessPercent: 10,
        lineTotal: 2870, // 3500 * 0.82
        marginPercent: 16.4,
        isSubscription: false,
        comments: ['Customer requested discount matching previous competitor quote.']
      },
      {
        id: 'ql-3',
        productId: 'prod-3',
        productName: 'Cloud Backup & Disaster Recovery',
        category: 'SUBSCRIPTION',
        quantity: 12,
        unitPrice: 450,
        unitCost: 90,
        discountPercent: 10,
        allowedDiscountCeiling: 15,
        discountExcessPercent: 0,
        lineTotal: 4860, // 12 * 450 * 0.90
        marginPercent: 77.8,
        isSubscription: true,
        recurringInterval: 'MONTHLY'
      }
    ],
    orderDiscountPercent: 2,
    subtotal: 33074,
    totalDiscountAmount: 4330,
    taxAmount: 2257,
    totalAmount: 34669.52,
    totalCost: 19080,
    blendedMarginPercent: 42.1,
    blendedRiskScore: 72,
    riskStatus: 'HIGH_RISK',
    riskReasons: [
      'Services line discount (18%) exceeds category ceiling (8%) by 10 percentage points',
      'Blended margin compression on implementation services below corporate safety floor (20%)',
      'Dual-tier threshold reached: triggers sequential Manager → Finance authorization'
    ],
    approvalRequired: true,
    requiredApprovalLevel: 'MANAGER_AND_FINANCE',
    currentApprovalStep: 'MANAGER'
  },
  {
    id: 'q-1049',
    quoteNumber: 'Q-1049',
    customerId: 'cust-2',
    customerName: 'NovaTech Industries',
    customerTier: 'SILVER',
    salesRepId: 'usr-1',
    salesRepName: 'Sarah Chen',
    createdAt: '2026-09-01T14:15:00Z',
    updatedAt: '2026-09-03T11:00:00Z',
    stage: 'UNDER_NEGOTIATION',
    lines: [
      {
        id: 'ql-4',
        productId: 'prod-2',
        productName: 'Network Security Appliance Pro',
        category: 'HARDWARE',
        quantity: 3,
        unitPrice: 3400,
        unitCost: 1900,
        discountPercent: 8,
        allowedDiscountCeiling: 10,
        discountExcessPercent: 0,
        lineTotal: 9384,
        marginPercent: 39.3,
        isSubscription: false
      },
      {
        id: 'ql-5',
        productId: 'prod-4',
        productName: 'Premium 24/7 Dedicated Support',
        category: 'SERVICES',
        quantity: 1,
        unitPrice: 1200,
        unitCost: 800,
        discountPercent: 5,
        allowedDiscountCeiling: 10,
        discountExcessPercent: 0,
        lineTotal: 1140,
        marginPercent: 29.8,
        isSubscription: true,
        recurringInterval: 'MONTHLY'
      }
    ],
    orderDiscountPercent: 0,
    subtotal: 10524,
    totalDiscountAmount: 876,
    taxAmount: 750.72,
    totalAmount: 11274.72,
    totalCost: 6500,
    blendedMarginPercent: 38.2,
    blendedRiskScore: 28,
    riskStatus: 'HEALTHY',
    riskReasons: ['All line discounts strictly comply with Silver customer & category discount policies.'],
    approvalRequired: false,
    requiredApprovalLevel: 'NONE',
    hasActiveNegotiation: true
  },
  {
    id: 'q-1050',
    quoteNumber: 'Q-1050',
    customerId: 'cust-3',
    customerName: 'Vertex Systems',
    customerTier: 'BRONZE',
    salesRepId: 'usr-1',
    salesRepName: 'Sarah Chen',
    createdAt: '2026-09-03T09:00:00Z',
    updatedAt: '2026-09-03T09:20:00Z',
    stage: 'DRAFT',
    lines: [
      {
        id: 'ql-6',
        productId: 'prod-1',
        productName: 'Enterprise Edge Server X4',
        category: 'HARDWARE',
        quantity: 2,
        unitPrice: 4800,
        unitCost: 2600,
        discountPercent: 4,
        allowedDiscountCeiling: 5,
        discountExcessPercent: 0,
        lineTotal: 9216,
        marginPercent: 43.6,
        isSubscription: false
      }
    ],
    orderDiscountPercent: 0,
    subtotal: 9216,
    totalDiscountAmount: 384,
    taxAmount: 737.28,
    totalAmount: 9953.28,
    totalCost: 5200,
    blendedMarginPercent: 43.6,
    blendedRiskScore: 15,
    riskStatus: 'HEALTHY',
    riskReasons: ['Healthy commercial parameters; no governance rules breached.'],
    approvalRequired: false,
    requiredApprovalLevel: 'NONE'
  },
  {
    id: 'q-1051',
    quoteNumber: 'Q-1051',
    customerId: 'cust-4',
    customerName: 'Orion Manufacturing',
    customerTier: 'PLATINUM',
    salesRepId: 'usr-1',
    salesRepName: 'Sarah Chen',
    createdAt: '2026-08-28T16:00:00Z',
    updatedAt: '2026-09-04T12:30:00Z',
    stage: 'CONFIRMED',
    lines: [
      {
        id: 'ql-7',
        productId: 'prod-1',
        productName: 'Enterprise Edge Server X4',
        category: 'HARDWARE',
        quantity: 10,
        unitPrice: 4800,
        unitCost: 2600,
        discountPercent: 14,
        allowedDiscountCeiling: 15,
        discountExcessPercent: 0,
        lineTotal: 41280,
        marginPercent: 37.0,
        isSubscription: false
      },
      {
        id: 'ql-8',
        productId: 'prod-6',
        productName: 'AI Inference Acceleration Module',
        category: 'HARDWARE',
        quantity: 4,
        unitPrice: 7500,
        unitCost: 4500,
        discountPercent: 8,
        allowedDiscountCeiling: 10,
        discountExcessPercent: 0,
        lineTotal: 27600,
        marginPercent: 34.8,
        isSubscription: false
      },
      {
        id: 'ql-9',
        productId: 'prod-3',
        productName: 'Cloud Backup & Disaster Recovery',
        category: 'SUBSCRIPTION',
        quantity: 24,
        unitPrice: 450,
        unitCost: 90,
        discountPercent: 12,
        allowedDiscountCeiling: 15,
        discountExcessPercent: 0,
        lineTotal: 9504,
        marginPercent: 77.3,
        isSubscription: true,
        recurringInterval: 'MONTHLY'
      }
    ],
    orderDiscountPercent: 1.5,
    subtotal: 78384,
    totalDiscountAmount: 11450,
    taxAmount: 5510,
    totalAmount: 82718.24,
    totalCost: 46160,
    blendedMarginPercent: 41.0,
    blendedRiskScore: 35,
    riskStatus: 'HEALTHY',
    riskReasons: ['Approved by VP of Sales on 2026-09-03.'],
    approvalRequired: true,
    requiredApprovalLevel: 'SALES_MANAGER',
    currentApprovalStep: 'COMPLETED'
  },
  {
    id: 'q-1045',
    quoteNumber: 'Q-1045',
    customerId: 'cust-2',
    customerName: 'NovaTech Industries',
    customerTier: 'SILVER',
    salesRepId: 'usr-1',
    salesRepName: 'Sarah Chen',
    createdAt: '2026-08-20T11:00:00Z',
    updatedAt: '2026-08-25T14:00:00Z',
    stage: 'RETURNED_FOR_REVISION',
    lines: [
      {
        id: 'ql-10',
        productId: 'prod-1',
        productName: 'Enterprise Edge Server X4',
        category: 'HARDWARE',
        quantity: 4,
        unitPrice: 4800,
        unitCost: 2600,
        discountPercent: 16,
        allowedDiscountCeiling: 10,
        discountExcessPercent: 6,
        lineTotal: 16128,
        marginPercent: 35.5,
        isSubscription: false
      }
    ],
    orderDiscountPercent: 0,
    subtotal: 16128,
    totalDiscountAmount: 3072,
    taxAmount: 1290.24,
    totalAmount: 17418.24,
    totalCost: 10400,
    blendedMarginPercent: 35.5,
    blendedRiskScore: 68,
    riskStatus: 'HIGH_RISK',
    riskReasons: ['Requested 16% discount on Silver tier (limit 10%). Returned by Sales Manager requesting bundle attach.'],
    approvalRequired: true,
    requiredApprovalLevel: 'SALES_MANAGER'
  }
];

export const mockApprovals: ApprovalInstance[] = [
  {
    id: 'app-1',
    quotationId: 'q-1048',
    quoteNumber: 'Q-1048',
    customerName: 'Acme Corporation',
    amount: 34669.52,
    riskScore: 72,
    status: 'PENDING',
    steps: [
      {
        id: 'step-1',
        stepNumber: 1,
        roleRequired: 'SALES_MANAGER',
        reviewerName: 'Marcus Vance',
        reviewerId: 'usr-2',
        status: 'PENDING',
        comment: 'Awaiting review of 18% services line discount.'
      },
      {
        id: 'step-2',
        stepNumber: 2,
        roleRequired: 'FINANCE_OPERATIONS',
        reviewerName: 'Elena Rostova',
        reviewerId: 'usr-3',
        status: 'PENDING',
        comment: 'Requires Finance review because risk score (72) exceeds 70 threshold.'
      }
    ],
    submittedAt: '2026-09-04T16:45:00Z',
    reasons: [
      'Custom Implementation discount is 18%, exceeding the 8% service ceiling by +10.0%',
      'Gross margin on line 2 is compressed to 16.4%, below the 20% floor',
      'Dual-threshold violation triggers mandatory 2-tier approval (Manager → Finance)'
    ],
    auditTimeline: [
      {
        id: 'aud-1',
        entityType: 'QUOTATION',
        entityId: 'q-1048',
        userName: 'Sarah Chen',
        userRole: 'Sales Representative',
        action: 'SUBMITTED_FOR_APPROVAL',
        timestamp: '2026-09-04T16:45:00Z',
        reason: 'Automated governance routing triggered by discount ceiling violation.',
        details: 'Discounts resolved. Blended risk calculated at 72 (High Risk).'
      }
    ]
  },
  {
    id: 'app-2',
    quotationId: 'q-1045',
    quoteNumber: 'Q-1045',
    customerName: 'NovaTech Industries',
    amount: 17418.24,
    riskScore: 68,
    status: 'REVISION_REQUIRED',
    steps: [
      {
        id: 'step-3',
        stepNumber: 1,
        roleRequired: 'SALES_MANAGER',
        reviewerName: 'Marcus Vance',
        reviewerId: 'usr-2',
        status: 'REVISION_REQUESTED',
        comment: 'Hardware discount too aggressive for a Silver customer. Please attach 1yr Cloud Backup to recover margin.',
        decidedAt: '2026-08-25T14:00:00Z'
      }
    ],
    submittedAt: '2026-08-24T09:15:00Z',
    reasons: ['Hardware discount 16% on Silver tier (limit 10%) without cross-sell margin offset.'],
    auditTimeline: [
      {
        id: 'aud-2',
        entityType: 'APPROVAL',
        entityId: 'app-2',
        userName: 'Marcus Vance',
        userRole: 'Sales Manager',
        action: 'RETURNED_FOR_REVISION',
        timestamp: '2026-08-25T14:00:00Z',
        reason: 'Requested margin recovery via subscription attach.',
        details: 'Quotation status changed to RETURNED_FOR_REVISION'
      }
    ]
  }
];

export const mockWarehouses: Warehouse[] = [
  {
    id: 'wh-1',
    name: 'Main Distribution Center',
    code: 'ORD-MAIN',
    city: 'Chicago, IL',
    shippingWeight: 1.0,
    stockByProduct: {
      'prod-1': 6, // Enterprise Edge Server
      'prod-2': 14,
      'prod-6': 2
    }
  },
  {
    id: 'wh-2',
    name: 'East Coast Depot',
    code: 'EWR-DEPOT',
    city: 'Newark, NJ',
    shippingWeight: 1.3,
    stockByProduct: {
      'prod-1': 4, // Remainder of 10 needed for Orion
      'prod-2': 5,
      'prod-6': 1 // 2 + 1 = 3 available; 4 required -> 1 backordered!
    }
  },
  {
    id: 'wh-3',
    name: 'West Logistics Hub',
    code: 'RNO-WEST',
    city: 'Reno, NV',
    shippingWeight: 1.4,
    stockByProduct: {
      'prod-1': 1,
      'prod-2': 8,
      'prod-6': 0
    }
  }
];

export const mockFulfillments: Record<string, OrderFulfillment> = {
  'ord-1051': {
    orderId: 'ord-1051',
    quotationId: 'q-1051',
    quoteNumber: 'Q-1051',
    customerName: 'Orion Manufacturing',
    status: 'SUGGESTED',
    allocations: [
      {
        warehouseId: 'wh-1',
        warehouseName: 'Main Distribution Center (Chicago)',
        productId: 'prod-1',
        productName: 'Enterprise Edge Server X4',
        quantityAllocated: 6,
        estimatedShipments: 1,
        estimatedCost: 380
      },
      {
        warehouseId: 'wh-2',
        warehouseName: 'East Coast Depot (Newark)',
        productId: 'prod-1',
        productName: 'Enterprise Edge Server X4',
        quantityAllocated: 4,
        estimatedShipments: 1,
        estimatedCost: 290
      },
      {
        warehouseId: 'wh-1',
        warehouseName: 'Main Distribution Center (Chicago)',
        productId: 'prod-6',
        productName: 'AI Inference Acceleration Module',
        quantityAllocated: 2,
        estimatedShipments: 1,
        estimatedCost: 140
      },
      {
        warehouseId: 'wh-2',
        warehouseName: 'East Coast Depot (Newark)',
        productId: 'prod-6',
        productName: 'AI Inference Acceleration Module',
        quantityAllocated: 1,
        estimatedShipments: 1,
        estimatedCost: 110
      }
    ],
    totalShipments: 2,
    totalShippingCost: 920,
    backorderQuantity: 1,
    backorderProductNames: ['AI Inference Acceleration Module (1 unit backordered)'],
    consolidationAvailable: true
  }
};

export const mockSubscriptions: SubscriptionItem[] = [
  {
    id: 'sub-1',
    orderId: 'ord-1051',
    productName: 'Cloud Backup & Disaster Recovery',
    quantity: 24,
    amount: 9504,
    interval: 'MONTHLY',
    startDate: '2026-09-01',
    nextBillingDate: '2026-10-01',
    status: 'ACTIVE'
  },
  {
    id: 'sub-2',
    orderId: 'ord-1049',
    productName: 'Premium 24/7 Dedicated Support',
    quantity: 1,
    amount: 1140,
    interval: 'MONTHLY',
    startDate: '2026-09-01',
    nextBillingDate: '2026-10-01',
    status: 'ACTIVE'
  }
];

export const mockInvoices: Invoice[] = [
  {
    id: 'inv-1001',
    invoiceNumber: 'INV-2026-0891',
    orderId: 'ord-1051',
    customerName: 'Orion Manufacturing',
    type: 'ONE_TIME',
    amount: 73214.24,
    paidAmount: 73214.24,
    status: 'PAID',
    dueDate: '2026-10-01',
    issuedAt: '2026-09-04'
  },
  {
    id: 'inv-1002',
    invoiceNumber: 'INV-2026-0892-REC1',
    orderId: 'ord-1051',
    customerName: 'Orion Manufacturing',
    type: 'RECURRING',
    amount: 9504.00,
    paidAmount: 0,
    status: 'ISSUED',
    dueDate: '2026-10-01',
    issuedAt: '2026-09-04'
  },
  {
    id: 'inv-1003',
    invoiceNumber: 'INV-2026-0740',
    orderId: 'ord-1042',
    customerName: 'Acme Corporation',
    type: 'ONE_TIME',
    amount: 42100.00,
    paidAmount: 20000.00,
    status: 'PARTIALLY_PAID',
    dueDate: '2026-09-15',
    issuedAt: '2026-08-15'
  }
];

export const mockDealAlerts: DealAlert[] = [
  {
    id: 'alt-1',
    quotationId: 'q-1048',
    quoteNumber: 'Q-1048',
    customerName: 'Acme Corporation',
    ownerName: 'Sarah Chen',
    type: 'DISCOUNT_ANOMALY',
    severity: 'HIGH',
    reason: 'Services discount is 18%, which is 2.4x higher than the rep\'s historical average of 7.5% for Services.',
    ageDays: 2,
    status: 'OPEN',
    suggestedAction: 'Require VP of Sales dual-signoff or adjust discount ceiling.'
  },
  {
    id: 'alt-2',
    quotationId: 'q-1045',
    quoteNumber: 'Q-1045',
    customerName: 'NovaTech Industries',
    ownerName: 'Sarah Chen',
    type: 'STALLED',
    severity: 'MEDIUM',
    reason: 'Quotation has been in "RETURNED_FOR_REVISION" status for 11 days with no rep activity logged.',
    ageDays: 11,
    status: 'OPEN',
    suggestedAction: 'Send automated reminder nudge to rep or reassign to tier lead.'
  },
  {
    id: 'alt-3',
    quotationId: 'q-1051',
    quoteNumber: 'Q-1051',
    customerName: 'Orion Manufacturing',
    ownerName: 'Sarah Chen',
    type: 'DELIVERY_SLIPPAGE',
    severity: 'MEDIUM',
    reason: '1 unit of AI Inference Acceleration Module is on backorder; promised delivery in 4 days risks slipping by 3 days.',
    ageDays: 1,
    status: 'ACKNOWLEDGED',
    suggestedAction: 'Execute consolidation from incoming East Depot replenishment batch.'
  }
];

export const mockGovernanceConfig: GovernanceConfig = {
  roleCeilings: {
    repCeiling: 10,
    managerCeiling: 20,
    financeCeiling: 35
  },
  tierDiscountCeilings: {
    BRONZE: 5,
    SILVER: 10,
    GOLD: 15,
    PLATINUM: 20
  },
  categoryDiscountCeilings: {
    HARDWARE: 15,
    SERVICES: 10,
    SUBSCRIPTION: 15
  },
  managerApprovalRiskThreshold: 45,
  financeApprovalRiskThreshold: 70,
  minCorporateMarginFloor: 25,
  riskWeights: {
    discountBreach: 40,
    marginDeviation: 35,
    paymentRisk: 25
  }
};

export const mockNegotiations: NegotiationRequest[] = [
  {
    id: 'neg-1',
    quotationId: 'q-1049',
    customerName: 'NovaTech Industries',
    requestedDiscountPercent: 12,
    notes: 'NovaTech procurement requests 12% on hardware to meet capital expenditure allocation constraints.',
    status: 'PENDING_REVIEW',
    createdAt: '2026-09-03T11:00:00Z',
    lineComments: [
      {
        lineId: 'ql-4',
        productName: 'Network Security Appliance Pro',
        comment: 'Can we get an additional 4% discount if we agree to a 2-year maintenance contract?'
      }
    ]
  }
];
