import React, { useState } from 'react';
import { 
  X, 
  CheckCircle2, 
  ArrowRight, 
  Sparkles, 
  ExternalLink,
  ShieldAlert,
  Layers,
  Truck,
  CreditCard,
  MessageSquareQuote,
  DollarSign
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const TestFlowGuideModal: React.FC = () => {
  const { 
    isGuideOpen, 
    setIsGuideOpen, 
    setCurrentPage, 
    setSelectedQuoteId, 
    setUserRole 
  } = useApp();

  const [activeStep, setActiveStep] = useState(0);

  if (!isGuideOpen) return null;

  const testSteps = [
    {
      id: 'AT-01',
      title: '1. Setup & Baseline Configuration',
      summary: 'Review customer discount tiers (Bronze 5%, Silver 10%, Gold 15%), warehouses, and subscription plans.',
      icon: Layers,
      actionLabel: 'Go to Administration',
      onAction: () => {
        setUserRole('ADMIN');
        setCurrentPage('admin');
        setIsGuideOpen(false);
      }
    },
    {
      id: 'AT-02',
      title: '2. Create Quote & Trigger Discount Violation',
      summary: 'Open Quote Q-1048 (Acme Corp - Gold). Notice Custom Implementation discount is 18%, exceeding the 8% service ceiling.',
      icon: ShieldAlert,
      actionLabel: 'Open Quote Builder',
      onAction: () => {
        setUserRole('SALES_REP');
        setSelectedQuoteId('q-1048');
        setCurrentPage('quote-builder');
        setIsGuideOpen(false);
      }
    },
    {
      id: 'AT-03',
      title: '3. Automated Approval Routing',
      summary: 'Click "Send for Approval". DealFlow Intelligence calculates risk (72/100) and automatically routes to Manager -> Finance without manual rep selection.',
      icon: CheckCircle2,
      actionLabel: 'Go to Approval Center',
      onAction: () => {
        setUserRole('SALES_MANAGER');
        setCurrentPage('approvals');
        setIsGuideOpen(false);
      }
    },
    {
      id: 'AT-04',
      title: '4. Upsell Suggestion & Live Margin Update',
      summary: 'In Quote Builder, click "Add to Quote" on the DealFlow Intelligence recommendation card (e.g. 24/7 Dedicated Support). Watch total and margin jump (+4.2%).',
      icon: Sparkles,
      actionLabel: 'View Quote Intelligence',
      onAction: () => {
        setUserRole('SALES_REP');
        setSelectedQuoteId('q-1048');
        setCurrentPage('quote-builder');
        setIsGuideOpen(false);
      }
    },
    {
      id: 'AT-05',
      title: '5. Multi-Warehouse Stock Split & Backorder',
      summary: 'Review Order ORD-1051 (Orion Mfg). The engine splits 10 Servers between Main Warehouse (6) and East Depot (4) with 1 backordered module.',
      icon: Truck,
      actionLabel: 'Open Warehouse Fulfillment',
      onAction: () => {
        setUserRole('FINANCE_OPERATIONS');
        setCurrentPage('fulfillment');
        setIsGuideOpen(false);
      }
    },
    {
      id: 'AT-06',
      title: '6. Hybrid Billing (One-time + Recurring)',
      summary: 'Examine hybrid billing showing separate One-Time hardware ($73,214) and Recurring cloud backup subscription ($9,504/mo) on the same order.',
      icon: CreditCard,
      actionLabel: 'Open Billing & Subscriptions',
      onAction: () => {
        setUserRole('FINANCE_OPERATIONS');
        setCurrentPage('billing');
        setIsGuideOpen(false);
      }
    },
    {
      id: 'AT-07',
      title: '7. Customer Portal Negotiation & Auto Re-Approval',
      summary: 'Switch to Customer view. Counter-propose a larger discount. The mock governance engine automatically catches the violation and routes for demo re-approval!',
      icon: MessageSquareQuote,
      actionLabel: 'Open Customer Portal',
      onAction: () => {
        setUserRole('CUSTOMER_PORTAL');
        setCurrentPage('portal');
        setIsGuideOpen(false);
      }
    },
    {
      id: 'AT-08',
      title: '8. Payment Recording & Realtime Invoice Status',
      summary: 'Record a customer payment against an issued invoice and watch status transition live from ISSUED to PARTIALLY_PAID or PAID.',
      icon: DollarSign,
      actionLabel: 'Go to Billing Payments',
      onAction: () => {
        setUserRole('FINANCE_OPERATIONS');
        setCurrentPage('billing');
        setIsGuideOpen(false);
      }
    }
  ];

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-2xl w-full overflow-hidden flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">8-Step Acceptance Test Walkthrough</h2>
              <p className="text-xs text-slate-500">Official Odoo Hackathon validation sequence from Section 9/Problem Statement</p>
            </div>
          </div>
          <button
            onClick={() => setIsGuideOpen(false)}
            className="w-8 h-8 rounded-lg hover:bg-slate-200 text-slate-500 hover:text-slate-800 flex items-center justify-center transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Steps List */}
        <div className="p-6 overflow-y-auto space-y-3 divide-y divide-slate-100">
          {testSteps.map((step, idx) => {
            const Icon = step.icon;
            const isCurrent = activeStep === idx;
            return (
              <div 
                key={step.id} 
                onClick={() => setActiveStep(idx)}
                className={`pt-3 first:pt-0 rounded-xl p-3.5 transition cursor-pointer ${
                  isCurrent ? 'bg-blue-50/70 border border-blue-200' : 'hover:bg-slate-50 border border-transparent'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                      isCurrent ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600'
                    }`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold px-1.5 py-0.2 rounded bg-slate-200/70 text-slate-700">
                          {step.id}
                        </span>
                        <h3 className="text-sm font-bold text-slate-900">{step.title}</h3>
                      </div>
                      <p className="text-xs text-slate-600 mt-1 leading-relaxed">{step.summary}</p>
                    </div>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      step.onAction();
                    }}
                    className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-300 hover:border-blue-500 text-slate-800 hover:text-blue-600 text-xs font-semibold shadow-2xs transition cursor-pointer"
                  >
                    <span>{step.actionLabel}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between text-xs text-slate-500">
          <span>The prototype faithfully simulates the complete FastAPI + PostgreSQL logic flow.</span>
          <button
            onClick={() => setIsGuideOpen(false)}
            className="px-4 py-1.5 rounded-lg bg-slate-900 text-white font-medium hover:bg-slate-800 transition cursor-pointer"
          >
            Close Guide
          </button>
        </div>
      </div>
    </div>
  );
};
