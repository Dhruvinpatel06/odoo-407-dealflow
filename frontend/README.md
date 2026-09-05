# DealFlow360 — Frontend Platform

**DealFlow360** is an intelligent, self-governing B2B sales operations platform featuring real-time discount governance, automated multi-level approval workflows, split-warehouse fulfillment optimization, and hybrid recurring billing.

---

## Technology Stack

- **Framework**: React 19 + TypeScript
- **Bundler & Dev Server**: Vite
- **Styling**: Tailwind CSS v4
- **State & Data Layer**: Client State + TanStack Query ready
- **Visualizations & Charts**: Recharts
- **Icons**: Lucide React

---

## Getting Started

### Prerequisites
- Node.js (v18+)
- npm

### Installation & Run
```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server (runs at http://localhost:3000)
npm run dev

# Run TypeScript validation
npm run lint

# Build production bundle
npm run build
```

---

## Evaluation Personas & Demo Accounts

All credentials work directly with 1-click quick-fill in the Demo Authentication screen:

| Role | Name | Email | Password | Scope & Primary Workflow |
| :--- | :--- | :--- | :--- | :--- |
| **Sales Rep** | Sarah Chen | `sales@dealflow360.io` | `sales123` | Quote builder, discount limits ≤ 10%, submit for review, counter customer terms |
| **Sales Manager** | Marcus Vance | `manager@dealflow360.io` | `manager123` | Level 1 approval, return for revision, tier discount governance, deal health |
| **Finance & Ops** | Elena Rostova | `finance@dealflow360.io` | `finance123` | Level 2 approval, margin breach sign-off, billing, payments, credit notes |
| **Fulfillment Lead** | Carlos Ruiz | `fulfillment@dealflow360.io` | `fulfillment123` | Warehouse split allocations, inventory override, backorder consolidation |
| **Platform Admin** | Alex Mercer | `admin@dealflow360.io` | `admin123` | System-wide 5-tab governance, catalog SKUs, warehouses, risk scoring weights |
| **Customer Portal** | David Kross (Acme Corp) | `customer@dealflow360.io` | `customer123` | External client view, line-level inquiry, propose counter-discounts, confirm |
