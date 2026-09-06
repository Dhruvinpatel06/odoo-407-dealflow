# DealFlow360 API Reference for Frontend

**Base URL**: `http://127.0.0.1:8000` (API Prefix: `/api/v1`)

## Authentication Notes

- Protected endpoints require Header: `Authorization: Bearer <access_token>`
- Refresh token is maintained via HttpOnly cookie `refresh_token` or auth refresh endpoint.
- Date/time formats are ISO 8601 strings (e.g., `2026-09-06T12:00:00Z`). UUIDs are standard RFC 4122 strings.


## APPROVALS (7 endpoints)

### `GET` /api/v1/approvals
**Summary**: List Approval Workflows
**Description**: List approval workflows visible to authorized roles.

**Query Parameters**:
- `status` (Optional[string], Optional): 
- `quotation_id` (Optional[string (uuid)], Optional): 
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `GET` /api/v1/approvals/pending
**Summary**: List Pending Approval Work Relevant to Current User
**Description**: Return pending approval steps the current user is authorized to act on.

---
### `GET` /api/v1/approvals/{id}
**Summary**: Get Approval Instance Details
**Description**: Return approval instance with its sequential reviewer steps.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/approvals/{id}/approve
**Summary**: Approve Current Approval Step
**Description**: Approve the current approval step in sequence.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{}
```

---
### `POST` /api/v1/approvals/{id}/reject
**Summary**: Reject Approval Workflow
**Description**: Reject the current approval step/workflow.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{}
```

---
### `POST` /api/v1/approvals/{id}/return-for-revision
**Summary**: Return Quotation for Revision
**Description**: Return quotation and approval workflow for revision.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{}
```

---
### `GET` /api/v1/approvals/{id}/audit-log
**Summary**: Get Approval Workflow Audit Log
**Description**: Return audit history related to approval workflow.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---

## BACKORDERS (4 endpoints)

### `GET` /api/v1/backorders
**Summary**: List Backorders
**Description**: List backorders with optional filters.

**Query Parameters**:
- `status` (Optional[enum: ['OPEN', 'CONSOLIDATION_AVAILABLE', 'CONSOLIDATED', 'FULFILLED', 'CANCELLED']], Optional): Filter by status
- `order_id` (Optional[string (uuid)], Optional): Filter by order UUID
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `GET` /api/v1/backorders/{id}
**Summary**: Get Backorder
**Description**: Return backorder details by UUID.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/backorders/{id}/consolidate
**Summary**: Consolidate Backorder
**Description**: Consolidate remaining backordered quantity using newly available inventory.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/backorders/{id}/cancel
**Summary**: Cancel Backorder
**Description**: Cancel open backorder.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---

## BILLING (3 endpoints)

### `GET` /api/v1/orders/{id}/billing
**Summary**: Get Order Billing
**Description**: Return complete billing state for an order (one-time + recurring).

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/orders/{id}/billing/generate
**Summary**: Generate Order Billing
**Description**: Generate one-time invoices and recurring subscriptions/schedules for an order.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/orders/{id}/credit-notes
**Summary**: Create Order Credit Note
**Description**: Issue a credit note against an order.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "amount": {
    "type": "number | string",
    "required": true,
    "description": "",
    "default": null,
    "nested": null
  },
  "reason": {
    "type": "Optional[string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  }
}
```

---

## BILLING SCHEDULES (4 endpoints)

### `GET` /api/v1/billing-schedules
**Summary**: List Billing Schedules
**Description**: List recurring billing schedule entries.

**Query Parameters**:
- `subscription_id` (Optional[string (uuid)], Optional): Filter by subscription
- `status` (Optional[enum: ['SCHEDULED', 'INVOICED', 'PAID', 'CANCELLED']], Optional): Filter by status
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `GET` /api/v1/billing-schedules/{id}
**Summary**: Get Billing Schedule
**Description**: Get billing schedule entry by UUID.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/billing-schedules/{id}/generate-invoice
**Summary**: Generate Invoice From Schedule
**Description**: Generate recurring invoice from scheduled billing event.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/billing-schedules/{id}/cancel
**Summary**: Cancel Billing Schedule
**Description**: Cancel scheduled billing event.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---

## FULFILLMENT (8 endpoints)

### `GET` /api/v1/orders/{id}/fulfillment
**Summary**: Get Order Fulfillment
**Description**: Return complete order fulfillment state.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/orders/{id}/fulfillment/suggest
**Summary**: Suggest Order Fulfillment
**Description**: Calculate recommended warehouse fulfillment split.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/orders/{id}/fulfillment/accept
**Summary**: Accept Order Fulfillment
**Description**: Accept the currently suggested warehouse split and reserve inventory.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `GET` /api/v1/orders/{id}/fulfillment/allocations
**Summary**: Get Order Allocations
**Description**: Return all fulfillment allocations for an order.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `PATCH` /api/v1/orders/{id}/fulfillment/allocations/{allocation_id}
**Summary**: Update Order Allocation
**Description**: Modify single allocation for manual fulfillment override.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier
- `allocation_id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "warehouse_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "quantity_allocated": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  }
}
```

---
### `POST` /api/v1/orders/{id}/fulfillment/override
**Summary**: Override Order Fulfillment
**Description**: Submit/confirm manual warehouse allocation override.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "allocations": {
    "type": "List[FulfillmentOverrideItem]",
    "required": true,
    "description": "",
    "default": null,
    "nested": [
      {
        "quotation_line_id": {
          "type": "string (uuid)",
          "required": true,
          "description": "",
          "default": null,
          "nested": null
        },
        "warehouse_id": {
          "type": "string (uuid)",
          "required": true,
          "description": "",
          "default": null,
          "nested": null
        },
        "quantity_allocated": {
          "type": "number | string",
          "required": true,
          "description": "",
          "default": null,
          "nested": null
        }
      }
    ]
  }
}
```

---
### `POST` /api/v1/orders/{id}/fulfillment/complete
**Summary**: Complete Order Fulfillment
**Description**: Mark fulfillment completed and deduct inventory stock.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `GET` /api/v1/orders/{id}/backorders
**Summary**: Get Order Backorders
**Description**: Return backorders belonging to an order.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---

## GENERAL (1 endpoints)

### `GET` /health
**Summary**: Health Check
**Description**: Liveness probe endpoint.

---

## INVENTORY (4 endpoints)

### `GET` /api/v1/inventory
**Summary**: List Inventory
**Description**: List inventory records with optional warehouse and product filters.

**Query Parameters**:
- `warehouse_id` (Optional[string (uuid)], Optional): Filter by warehouse
- `product_id` (Optional[string (uuid)], Optional): Filter by product
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `GET` /api/v1/inventory/{id}
**Summary**: Get Inventory Record
**Description**: Return single inventory record by UUID.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `PATCH` /api/v1/inventory/{id}
**Summary**: Update Inventory
**Description**: Update inventory quantities or replenishment configuration.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "quantity_on_hand": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "quantity_reserved": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "reorder_level": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "reorder_quantity": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  }
}
```

---
### `GET` /api/v1/inventory/product/{product_id}
**Summary**: Get Product Inventory
**Description**: Return product inventory across all active warehouses with available stock.

**Path Parameters**:
- `product_id` (string (uuid)): Resource identifier

---

## INVOICES (7 endpoints)

### `GET` /api/v1/invoices
**Summary**: List Invoices
**Description**: List invoices.

**Query Parameters**:
- `order_id` (Optional[string (uuid)], Optional): Filter by order
- `status` (Optional[enum: ['DRAFT', 'ISSUED', 'PARTIALLY_PAID', 'PAID', 'CANCELLED']], Optional): Filter by status
- `invoice_type` (Optional[enum: ['ONE_TIME', 'RECURRING', 'CREDIT_NOTE']], Optional): Filter by type
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `GET` /api/v1/invoices/{id}
**Summary**: Get Invoice
**Description**: Get invoice details by UUID.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/invoices/{id}/issue
**Summary**: Issue Invoice
**Description**: Issue draft invoice.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/invoices/{id}/cancel
**Summary**: Cancel Invoice
**Description**: Cancel invoice.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `GET` /api/v1/invoices/{id}/payments
**Summary**: Get Invoice Payments
**Description**: Return all payments recorded against an invoice.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/invoices/{id}/payments
**Summary**: Record Invoice Payment
**Description**: Record payment against invoice with overpayment protection.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "amount": {
    "type": "number | string",
    "required": true,
    "description": "",
    "default": null,
    "nested": null
  },
  "payment_method": {
    "type": "string",
    "required": true,
    "description": "",
    "default": null,
    "nested": null
  },
  "transaction_reference": {
    "type": "Optional[string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  }
}
```

---
### `GET` /api/v1/invoices/{id}/credit-notes
**Summary**: Get Invoice Credit Notes
**Description**: Return credit notes for an invoice/order.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---

## ORDERS (4 endpoints)

### `GET` /api/v1/orders
**Summary**: List Orders
**Description**: List confirmed sales orders with optional filters.

**Query Parameters**:
- `customer_id` (Optional[string (uuid)], Optional): Filter by customer UUID
- `status` (Optional[string], Optional): Filter by order status
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `GET` /api/v1/orders/{id}
**Summary**: Get Order
**Description**: Return complete order details by UUID.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `PATCH` /api/v1/orders/{id}
**Summary**: Update Order
**Description**: Update permitted order fields/state.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "status": {
    "type": "Optional[string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  }
}
```

---
### `GET` /api/v1/orders/{id}/audit-log
**Summary**: Get Order Audit Log
**Description**: Return order audit history.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---

## PAYMENTS (3 endpoints)

### `GET` /api/v1/payments
**Summary**: List Payments
**Description**: List recorded payments.

**Query Parameters**:
- `invoice_id` (Optional[string (uuid)], Optional): Filter by invoice
- `status` (Optional[enum: ['RECORDED', 'FAILED', 'REFUNDED']], Optional): Filter by status
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `GET` /api/v1/payments/{id}
**Summary**: Get Payment
**Description**: Get payment details by UUID.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/payments/{id}/refund
**Summary**: Refund Payment
**Description**: Refund a recorded payment and adjust invoice balance and status.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---

## PIPELINE (1 endpoints)

### `GET` /api/v1/pipeline
**Summary**: Get Sales Pipeline
**Description**: Return Kanban-style quotation/deal pipeline data.

---

## QUOTATIONS (18 endpoints)

### `GET` /api/v1/quotations
**Summary**: List Quotations
**Description**: List quotations with optional filtering.

**Query Parameters**:
- `status` (Optional[enum: ['DRAFT', 'SENT', 'UNDER_NEGOTIATION', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'REVISION_REQUIRED', 'CONFIRMED']], Optional): Filter by quotation status
- `customer_id` (Optional[string (uuid)], Optional): Filter by customer UUID
- `sales_rep_id` (Optional[string (uuid)], Optional): Filter by sales rep UUID
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `POST` /api/v1/quotations
**Summary**: Create Quotation
**Description**: Create a new draft quotation for a customer.

**Request Body (JSON)**:
```json
{
  "customer_id": {
    "type": "string (uuid)",
    "required": true,
    "description": "",
    "default": null,
    "nested": null
  },
  "valid_until": {
    "type": "Optional[string (date)]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  }
}
```

---
### `GET` /api/v1/quotations/{id}
**Summary**: Get Quotation
**Description**: Retrieve full quotation details including lines and latest calculated financial state.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `PATCH` /api/v1/quotations/{id}
**Summary**: Update Quotation
**Description**: Update allowed quotation metadata.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "valid_until": {
    "type": "Optional[string (date)]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  }
}
```

---
### `DELETE` /api/v1/quotations/{id}
**Summary**: Delete Quotation
**Description**: Delete draft quotation where allowed.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `GET` /api/v1/quotations/{id}/lines
**Summary**: Get Quotation Lines
**Description**: Retrieve all quotation lines for a quotation.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/quotations/{id}/lines
**Summary**: Add Quotation Line
**Description**: Add a product/variant line to a quotation and trigger complete server recalculation.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "product_id": {
    "type": "string (uuid)",
    "required": true,
    "description": "",
    "default": null,
    "nested": null
  },
  "variant_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "quantity": {
    "type": "number | string",
    "required": true,
    "description": "",
    "default": null,
    "nested": null
  },
  "unit_price": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "discount_percent": {
    "type": "number | string",
    "required": false,
    "description": "",
    "default": "0.00",
    "nested": null
  },
  "tax_rate": {
    "type": "number | string",
    "required": false,
    "description": "",
    "default": "0.00",
    "nested": null
  },
  "description": {
    "type": "Optional[string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  }
}
```

---
### `PATCH` /api/v1/quotations/{id}/lines/{line_id}
**Summary**: Update Quotation Line
**Description**: Update line-level values (quantity, discount, etc.) and recalculate dependent quotation state.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier
- `line_id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "quantity": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "unit_price": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "discount_percent": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "tax_rate": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "description": {
    "type": "Optional[string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  }
}
```

---
### `DELETE` /api/v1/quotations/{id}/lines/{line_id}
**Summary**: Delete Quotation Line
**Description**: Remove a quotation line and trigger complete quotation recalculation.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier
- `line_id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/quotations/{id}/recalculate
**Summary**: Recalculate Quotation
**Description**: Trigger full authoritative quotation recalculation across line pricing, discount governance,
totals, margin, blended risk score, and approval requirement.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `GET` /api/v1/quotations/{id}/risk
**Summary**: Get Quotation Risk
**Description**: Return authoritative quotation discount-risk state, blended risk score,
approval requirement, and line-level discount limits/excess for UI explanation.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/quotations/{id}/submit
**Summary**: Submit Quotation
**Description**: Submit quotation into the next workflow state.
Recalculates server-side first, then automatically determines approval requirement.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/quotations/{id}/send
**Summary**: Send Quotation
**Description**: Mark quotation as sent to customer.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/quotations/{id}/return-for-revision
**Summary**: Return Quotation For Revision
**Description**: Return quotation to revision state.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/quotations/{id}/confirm
**Summary**: Confirm Quotation
**Description**: Confirm quotation and generate corresponding confirmed sales order.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `GET` /api/v1/quotations/{id}/order
**Summary**: Get Quotation Order
**Description**: Return order generated from the quotation.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `GET` /api/v1/quotations/{id}/approvals
**Summary**: Get Quotation Approvals
**Description**: Return approval history and current approval workflow for quotation.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `GET` /api/v1/quotations/{id}/audit-log
**Summary**: Get Quotation Audit Log
**Description**: Return quotation-specific audit history.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---

## SUBSCRIPTION PLANS (5 endpoints)

### `GET` /api/v1/subscription-plans
**Summary**: List Subscription Plans
**Description**: List recurring subscription plans.

**Query Parameters**:
- `is_active` (Optional[boolean], Optional): Filter by active status
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `POST` /api/v1/subscription-plans
**Summary**: Create Subscription Plan
**Description**: Create a recurring subscription plan.

**Request Body (JSON)**:
```json
{
  "name": {
    "type": "string",
    "required": true,
    "description": "",
    "default": null,
    "nested": null
  },
  "billing_interval": {
    "type": "enum: ['MONTHLY', 'QUARTERLY', 'YEARLY']",
    "required": true,
    "description": "",
    "default": null,
    "nested": null
  },
  "interval_count": {
    "type": "integer",
    "required": false,
    "description": "",
    "default": 1,
    "nested": null
  },
  "proration_method": {
    "type": "enum: ['DAILY_PRO_RATA', 'FULL_PERIOD', 'NO_PRORATION']",
    "required": false,
    "description": "",
    "default": "DAILY_PRO_RATA",
    "nested": null
  },
  "cancellation_policy": {
    "type": "string",
    "required": false,
    "description": "",
    "default": "IMMEDIATE",
    "nested": null
  },
  "refund_policy": {
    "type": "string",
    "required": false,
    "description": "",
    "default": "PRO_RATA",
    "nested": null
  },
  "is_active": {
    "type": "boolean",
    "required": false,
    "description": "",
    "default": true,
    "nested": null
  }
}
```

---
### `GET` /api/v1/subscription-plans/{id}
**Summary**: Get Subscription Plan
**Description**: Get subscription plan details by UUID.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `PATCH` /api/v1/subscription-plans/{id}
**Summary**: Update Subscription Plan
**Description**: Update subscription plan configuration.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "name": {
    "type": "Optional[string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "billing_interval": {
    "type": "Optional[enum: ['MONTHLY', 'QUARTERLY', 'YEARLY']]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "interval_count": {
    "type": "Optional[integer]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "proration_method": {
    "type": "Optional[enum: ['DAILY_PRO_RATA', 'FULL_PERIOD', 'NO_PRORATION']]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "cancellation_policy": {
    "type": "Optional[string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "refund_policy": {
    "type": "Optional[string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "is_active": {
    "type": "Optional[boolean]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  }
}
```

---
### `DELETE` /api/v1/subscription-plans/{id}
**Summary**: Deactivate Subscription Plan
**Description**: Deactivate subscription plan.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---

## SUBSCRIPTIONS (8 endpoints)

### `GET` /api/v1/subscriptions
**Summary**: List Subscriptions
**Description**: List customer subscriptions.

**Query Parameters**:
- `customer_id` (Optional[string (uuid)], Optional): Filter by customer
- `status` (Optional[enum: ['ACTIVE', 'MODIFIED', 'CANCELLED', 'PAUSED']], Optional): Filter by status
- `order_id` (Optional[string (uuid)], Optional): Filter by order
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `GET` /api/v1/subscriptions/{id}
**Summary**: Get Subscription
**Description**: Get subscription details by UUID.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/subscriptions/{id}/modify
**Summary**: Modify Subscription
**Description**: Modify subscription quantity, plan, or price.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "quantity": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "plan_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "unit_price": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "effective_date": {
    "type": "Optional[string (date)]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  }
}
```

---
### `POST` /api/v1/subscriptions/{id}/cancel
**Summary**: Cancel Subscription
**Description**: Cancel subscription with optional credit-note generation.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "reason": {
    "type": "Optional[string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "issue_credit_note": {
    "type": "boolean",
    "required": false,
    "description": "",
    "default": false,
    "nested": null
  }
}
```

---
### `POST` /api/v1/subscriptions/{id}/pause
**Summary**: Pause Subscription
**Description**: Pause an active subscription.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/subscriptions/{id}/proration/preview
**Summary**: Preview Subscription Proration
**Description**: Calculate non-mutating preview of mid-cycle proration adjustment.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "new_quantity": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "new_plan_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "new_unit_price": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "effective_date": {
    "type": "Optional[string (date)]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  }
}
```

---
### `POST` /api/v1/subscriptions/{id}/proration/apply
**Summary**: Apply Subscription Proration
**Description**: Apply evaluated proration adjustment to subscription.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "new_quantity": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "new_plan_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "new_unit_price": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "effective_date": {
    "type": "Optional[string (date)]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "issue_credit_note": {
    "type": "boolean",
    "required": false,
    "description": "",
    "default": true,
    "nested": null
  }
}
```

---
### `POST` /api/v1/subscriptions/{id}/credit-note
**Summary**: Generate Subscription Credit Note
**Description**: Generate a credit note for subscription balance adjustment.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---

## WAREHOUSES (7 endpoints)

### `GET` /api/v1/warehouses
**Summary**: List Warehouses
**Description**: List fulfillment warehouses.

**Query Parameters**:
- `is_active` (Optional[boolean], Optional): Filter by active status
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `POST` /api/v1/warehouses
**Summary**: Create Warehouse
**Description**: Create a new fulfillment warehouse.

**Request Body (JSON)**:
```json
{
  "name": {
    "type": "string",
    "required": true,
    "description": "",
    "default": null,
    "nested": null
  },
  "code": {
    "type": "string",
    "required": true,
    "description": "",
    "default": null,
    "nested": null
  },
  "address": {
    "type": "Optional[string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "shipping_cost_weight": {
    "type": "number | string",
    "required": false,
    "description": "",
    "default": "1.00",
    "nested": null
  },
  "replenishment_enabled": {
    "type": "boolean",
    "required": false,
    "description": "",
    "default": false,
    "nested": null
  },
  "is_active": {
    "type": "boolean",
    "required": false,
    "description": "",
    "default": true,
    "nested": null
  }
}
```

---
### `GET` /api/v1/warehouses/{id}
**Summary**: Get Warehouse
**Description**: Get warehouse details by UUID.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `PATCH` /api/v1/warehouses/{id}
**Summary**: Update Warehouse
**Description**: Update warehouse configuration.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "name": {
    "type": "Optional[string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "code": {
    "type": "Optional[string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "address": {
    "type": "Optional[string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "shipping_cost_weight": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "replenishment_enabled": {
    "type": "Optional[boolean]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  },
  "is_active": {
    "type": "Optional[boolean]",
    "required": false,
    "description": "",
    "default": null,
    "nested": null
  }
}
```

---
### `DELETE` /api/v1/warehouses/{id}
**Summary**: Deactivate Warehouse
**Description**: Deactivate warehouse (soft delete).

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `GET` /api/v1/warehouses/{warehouse_id}/inventory
**Summary**: Get Warehouse Inventory
**Description**: Return inventory records for a specific warehouse.

**Path Parameters**:
- `warehouse_id` (string (uuid)): Resource identifier

**Query Parameters**:
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `POST` /api/v1/warehouses/{warehouse_id}/inventory
**Summary**: Configure Warehouse Inventory
**Description**: Create or set inventory configuration for a product in warehouse.

**Path Parameters**:
- `warehouse_id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "product_id": {
    "type": "string (uuid)",
    "required": true,
    "description": "",
    "default": null,
    "nested": null
  },
  "quantity_on_hand": {
    "type": "number | string",
    "required": false,
    "description": "",
    "default": "0.00",
    "nested": null
  },
  "reorder_level": {
    "type": "number | string",
    "required": false,
    "description": "",
    "default": "0.00",
    "nested": null
  },
  "reorder_quantity": {
    "type": "number | string",
    "required": false,
    "description": "",
    "default": "0.00",
    "nested": null
  }
}
```

---

## APPROVAL-POLICIES (5 endpoints)

### `GET` /api/v1/approval-policies
**Summary**: List Approval Policies
**Description**: List configurable approval policies with optional active status filter.

**Query Parameters**:
- `is_active` (Optional[boolean], Optional): 
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `POST` /api/v1/approval-policies
**Summary**: Create Approval Policy
**Description**: Create a new configurable approval policy. Admin and Sales Manager operation.

**Request Body (JSON)**:
```json
{
  "name": {
    "type": "string",
    "required": true,
    "description": "Human-readable approval policy name.",
    "default": null,
    "nested": null
  },
  "min_risk_score": {
    "type": "number | string",
    "required": true,
    "description": "Minimum risk score covered by policy.",
    "default": null,
    "nested": null
  },
  "max_risk_score": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "Maximum risk score covered by policy; null indicates no upper bound.",
    "default": null,
    "nested": null
  },
  "requires_manager": {
    "type": "boolean",
    "required": false,
    "description": "Indicates whether Sales Manager approval is required.",
    "default": false,
    "nested": null
  },
  "requires_finance": {
    "type": "boolean",
    "required": false,
    "description": "Indicates whether Finance/Operations approval is required.",
    "default": false,
    "nested": null
  },
  "priority": {
    "type": "integer",
    "required": false,
    "description": "Policy evaluation precedence (higher number = higher priority).",
    "default": 0,
    "nested": null
  },
  "is_active": {
    "type": "boolean",
    "required": false,
    "description": "Whether policy participates in evaluation.",
    "default": true,
    "nested": null
  }
}
```

---
### `GET` /api/v1/approval-policies/{id}
**Summary**: Get Approval Policy Details
**Description**: Return approval policy details by UUID.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `PATCH` /api/v1/approval-policies/{id}
**Summary**: Update Approval Policy
**Description**: Update approval policy configuration. Admin and Sales Manager operation.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "name": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated approval policy name.",
    "default": null,
    "nested": null
  },
  "min_risk_score": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "Updated minimum risk score.",
    "default": null,
    "nested": null
  },
  "max_risk_score": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "Updated maximum risk score; null represents no upper bound.",
    "default": null,
    "nested": null
  },
  "requires_manager": {
    "type": "Optional[boolean]",
    "required": false,
    "description": "Updated Sales Manager approval requirement.",
    "default": null,
    "nested": null
  },
  "requires_finance": {
    "type": "Optional[boolean]",
    "required": false,
    "description": "Updated Finance/Operations approval requirement.",
    "default": null,
    "nested": null
  },
  "priority": {
    "type": "Optional[integer]",
    "required": false,
    "description": "Updated evaluation precedence.",
    "default": null,
    "nested": null
  },
  "is_active": {
    "type": "Optional[boolean]",
    "required": false,
    "description": "Updated active status.",
    "default": null,
    "nested": null
  }
}
```

---
### `DELETE` /api/v1/approval-policies/{id}
**Summary**: Deactivate Approval Policy
**Description**: Deactivate an approval policy following logical-deactivation convention. Admin and Sales Manager operation.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---

## AUTH (6 endpoints)

### `POST` /api/v1/auth/signup
**Summary**: Customer Public Signup
**Description**: Public customer registration.
Creates a new user with role=CUSTOMER, active=True, and customer_id=None.
Client-supplied role is not permitted.

**Request Body (JSON)**:
```json
{
  "name": {
    "type": "string",
    "required": true,
    "description": "Full name",
    "default": null,
    "nested": null
  },
  "email": {
    "type": "string",
    "required": true,
    "description": "Email address",
    "default": null,
    "nested": null
  },
  "password": {
    "type": "string",
    "required": true,
    "description": "Password with minimum 8 characters",
    "default": null,
    "nested": null
  }
}
```

---
### `POST` /api/v1/auth/login
**Summary**: User Login
**Description**: Authenticate user credentials, start persistent auth session,
return short-lived access token, and attach refresh token cookie.

**Request Body (JSON)**:
```json
{
  "email": {
    "type": "string",
    "required": true,
    "description": "User email address",
    "default": null,
    "nested": null
  },
  "password": {
    "type": "string",
    "required": true,
    "description": "Plaintext password",
    "default": null,
    "nested": null
  }
}
```

---
### `POST` /api/v1/auth/refresh
**Summary**: Rotate Refresh Token
**Description**: Validate refresh token from cookie, rotate refresh token, and return new access token.

---
### `POST` /api/v1/auth/logout
**Summary**: User Logout
**Description**: Revoke current refresh session and clear the refresh token cookie.

---
### `GET` /api/v1/auth/me
**Summary**: Get Current User Profile
**Description**: Return authenticated user profile without exposing credentials or sensitive tokens.

---
### `POST` /api/v1/auth/change-password
**Summary**: Change User Password
**Description**: Verify current password, store new Argon2id hash, and revoke existing sessions.

**Request Body (JSON)**:
```json
{
  "current_password": {
    "type": "string",
    "required": true,
    "description": "",
    "default": null,
    "nested": null
  },
  "new_password": {
    "type": "string",
    "required": true,
    "description": "New password with minimum 8 characters",
    "default": null,
    "nested": null
  }
}
```

---

## CUSTOMER-TIERS (5 endpoints)

### `GET` /api/v1/customer-tiers
**Summary**: List Customer Tiers
**Description**: List customer tiers with optional active status filtering.

**Query Parameters**:
- `is_active` (Optional[boolean], Optional): 
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `POST` /api/v1/customer-tiers
**Summary**: Create Customer Tier
**Description**: Create a new customer tier.

**Request Body (JSON)**:
```json
{
  "name": {
    "type": "string",
    "required": true,
    "description": "Customer tier name (e.g., Bronze, Silver, Gold).",
    "default": null,
    "nested": null
  },
  "description": {
    "type": "Optional[string]",
    "required": false,
    "description": "Optional customer tier description.",
    "default": null,
    "nested": null
  },
  "default_discount_limit": {
    "type": "number | string",
    "required": true,
    "description": "Default maximum discount percentage ceiling for the tier.",
    "default": null,
    "nested": null
  },
  "is_active": {
    "type": "boolean",
    "required": false,
    "description": "Whether the customer tier is active.",
    "default": true,
    "nested": null
  }
}
```

---
### `GET` /api/v1/customer-tiers/{id}
**Summary**: Get Customer Tier
**Description**: Retrieve a customer tier by ID.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `PATCH` /api/v1/customer-tiers/{id}
**Summary**: Update Customer Tier
**Description**: Update a customer tier configuration.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "name": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated customer tier name.",
    "default": null,
    "nested": null
  },
  "description": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated customer tier description.",
    "default": null,
    "nested": null
  },
  "default_discount_limit": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "Updated default maximum discount percentage ceiling.",
    "default": null,
    "nested": null
  },
  "is_active": {
    "type": "Optional[boolean]",
    "required": false,
    "description": "Updated active status of the customer tier.",
    "default": null,
    "nested": null
  }
}
```

---
### `DELETE` /api/v1/customer-tiers/{id}
**Summary**: Deactivate Customer Tier
**Description**: Deactivate a customer tier following logical-deactivation convention.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---

## CUSTOMERS (8 endpoints)

### `GET` /api/v1/customers
**Summary**: List/Search Customers
**Description**: List and search B2B customers.
Used by Sales Rep quotation creation and administrative screens.
Defaults to returning active customers only.

**Query Parameters**:
- `search` (Optional[string], Optional): 
- `customer_tier_id` (Optional[string (uuid)], Optional): 
- `is_active` (Optional[boolean], Optional): 
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `POST` /api/v1/customers
**Summary**: Create Customer
**Description**: Create a new B2B customer/account record.
Accessible to ADMIN, SALES_MANAGER, and SALES_REP.

**Request Body (JSON)**:
```json
{
  "name": {
    "type": "string",
    "required": true,
    "description": "Customer or company name.",
    "default": null,
    "nested": null
  },
  "email": {
    "type": "Optional[string]",
    "required": false,
    "description": "Primary customer contact email.",
    "default": null,
    "nested": null
  },
  "phone": {
    "type": "Optional[string]",
    "required": false,
    "description": "Primary customer contact phone.",
    "default": null,
    "nested": null
  },
  "customer_tier_id": {
    "type": "string (uuid)",
    "required": true,
    "description": "UUID of the associated customer tier.",
    "default": null,
    "nested": null
  },
  "billing_address": {
    "type": "Optional[string]",
    "required": false,
    "description": "Customer billing address.",
    "default": null,
    "nested": null
  },
  "shipping_address": {
    "type": "Optional[string]",
    "required": false,
    "description": "Default customer shipping address.",
    "default": null,
    "nested": null
  },
  "is_active": {
    "type": "boolean",
    "required": false,
    "description": "Whether the customer is active.",
    "default": true,
    "nested": null
  }
}
```

---
### `GET` /api/v1/customers/{id}
**Summary**: Get Customer Details
**Description**: Retrieve customer details including customer tier association.
Accessible to ADMIN, SALES_MANAGER, SALES_REP, and FINANCE_OPERATIONS.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `PATCH` /api/v1/customers/{id}
**Summary**: Update Customer
**Description**: Update an existing B2B customer record.
Accessible to ADMIN, SALES_MANAGER, and SALES_REP.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "name": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated customer or company name.",
    "default": null,
    "nested": null
  },
  "email": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated primary contact email.",
    "default": null,
    "nested": null
  },
  "phone": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated primary contact phone.",
    "default": null,
    "nested": null
  },
  "customer_tier_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "Updated associated customer tier UUID.",
    "default": null,
    "nested": null
  },
  "billing_address": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated billing address.",
    "default": null,
    "nested": null
  },
  "shipping_address": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated default shipping address.",
    "default": null,
    "nested": null
  },
  "is_active": {
    "type": "Optional[boolean]",
    "required": false,
    "description": "Updated active status.",
    "default": null,
    "nested": null
  }
}
```

---
### `DELETE` /api/v1/customers/{id}
**Summary**: Deactivate Customer
**Description**: Deactivate a customer following logical-deactivation convention.
Accessible to ADMIN and SALES_MANAGER.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `GET` /api/v1/customers/{id}/quotations
**Summary**: Get Customer Quotation History
**Description**: Retrieve quotation history belonging to a specific customer.
Accessible to ADMIN, SALES_MANAGER, SALES_REP, and FINANCE_OPERATIONS.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Query Parameters**:
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `GET` /api/v1/customers/{id}/orders
**Summary**: Get Customer Order History
**Description**: Retrieve order history belonging to a specific customer.
Accessible to ADMIN, SALES_MANAGER, SALES_REP, and FINANCE_OPERATIONS.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Query Parameters**:
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `GET` /api/v1/customers/{id}/subscriptions
**Summary**: Get Customer Subscription History
**Description**: Retrieve subscription history belonging to a specific customer.
Accessible to ADMIN, SALES_MANAGER, SALES_REP, and FINANCE_OPERATIONS.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Query Parameters**:
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---

## DISCOUNT-RULES (5 endpoints)

### `GET` /api/v1/discount-rules
**Summary**: List Discount Rules
**Description**: List configurable discount rules with optional customer tier, category, and active status filters.

**Query Parameters**:
- `customer_tier_id` (Optional[string (uuid)], Optional): 
- `category_id` (Optional[string (uuid)], Optional): 
- `is_active` (Optional[boolean], Optional): 
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `POST` /api/v1/discount-rules
**Summary**: Create Discount Rule
**Description**: Create a new configurable discount rule. Admin-only operation.

**Request Body (JSON)**:
```json
{
  "customer_tier_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "Optional customer tier UUID condition.",
    "default": null,
    "nested": null
  },
  "category_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "Optional product category UUID condition.",
    "default": null,
    "nested": null
  },
  "max_discount_percent": {
    "type": "number | string",
    "required": true,
    "description": "Maximum permitted discount percentage ceiling (0.00 to 100.00).",
    "default": null,
    "nested": null
  },
  "priority": {
    "type": "integer",
    "required": false,
    "description": "Rule precedence when multiple rules apply (higher integer = higher priority).",
    "default": 0,
    "nested": null
  },
  "is_active": {
    "type": "boolean",
    "required": false,
    "description": "Whether rule participates in evaluation.",
    "default": true,
    "nested": null
  }
}
```

---
### `GET` /api/v1/discount-rules/{id}
**Summary**: Get Discount Rule Details
**Description**: Return discount rule details by UUID.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `PATCH` /api/v1/discount-rules/{id}
**Summary**: Update Discount Rule
**Description**: Update discount rule configuration. Admin-only operation.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "customer_tier_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "Updated customer tier UUID condition.",
    "default": null,
    "nested": null
  },
  "category_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "Updated product category UUID condition.",
    "default": null,
    "nested": null
  },
  "max_discount_percent": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "Updated maximum permitted discount percentage ceiling (0.00 to 100.00).",
    "default": null,
    "nested": null
  },
  "priority": {
    "type": "Optional[integer]",
    "required": false,
    "description": "Updated rule precedence.",
    "default": null,
    "nested": null
  },
  "is_active": {
    "type": "Optional[boolean]",
    "required": false,
    "description": "Updated active status.",
    "default": null,
    "nested": null
  }
}
```

---
### `DELETE` /api/v1/discount-rules/{id}
**Summary**: Deactivate Discount Rule
**Description**: Deactivate a discount rule following logical-deactivation convention. Admin-only operation.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---

## PRICING (10 endpoints)

### `GET` /api/v1/price-lists
**Summary**: List Price Lists
**Description**: List price lists with optional customer tier, currency, and active filters.

**Query Parameters**:
- `customer_tier_id` (Optional[string (uuid)], Optional): 
- `currency` (Optional[string], Optional): 
- `is_active` (Optional[boolean], Optional): 
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `POST` /api/v1/price-lists
**Summary**: Create Price List
**Description**: Create a new price list. Admin-only operation.

**Request Body (JSON)**:
```json
{
  "name": {
    "type": "string",
    "required": true,
    "description": "Price list name.",
    "default": null,
    "nested": null
  },
  "customer_tier_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "Optional customer tier UUID associated with this price list.",
    "default": null,
    "nested": null
  },
  "currency": {
    "type": "string",
    "required": false,
    "description": "ISO currency code (e.g. USD, EUR, INR).",
    "default": "USD",
    "nested": null
  },
  "is_active": {
    "type": "boolean",
    "required": false,
    "description": "Whether price list is active.",
    "default": true,
    "nested": null
  }
}
```

---
### `GET` /api/v1/price-lists/{id}
**Summary**: Get Price List Details
**Description**: Return price list details by UUID.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `PATCH` /api/v1/price-lists/{id}
**Summary**: Update Price List
**Description**: Update price list configuration. Admin-only operation.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "name": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated price list name.",
    "default": null,
    "nested": null
  },
  "customer_tier_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "Updated associated customer tier UUID.",
    "default": null,
    "nested": null
  },
  "currency": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated ISO currency code.",
    "default": null,
    "nested": null
  },
  "is_active": {
    "type": "Optional[boolean]",
    "required": false,
    "description": "Updated active status.",
    "default": null,
    "nested": null
  }
}
```

---
### `DELETE` /api/v1/price-lists/{id}
**Summary**: Deactivate Price List
**Description**: Deactivate a price list following logical-deactivation convention.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `GET` /api/v1/price-lists/{id}/items
**Summary**: List Price List Items
**Description**: List product/variant prices within a price list.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Query Parameters**:
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `POST` /api/v1/price-lists/{id}/items
**Summary**: Add Price List Item
**Description**: Add product/variant pricing override to a price list.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "product_id": {
    "type": "string (uuid)",
    "required": true,
    "description": "Product UUID.",
    "default": null,
    "nested": null
  },
  "variant_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "Optional product variant UUID.",
    "default": null,
    "nested": null
  },
  "price": {
    "type": "number | string",
    "required": true,
    "description": "Override unit selling price in this price list.",
    "default": null,
    "nested": null
  }
}
```

---
### `PATCH` /api/v1/price-lists/{id}/items/{item_id}
**Summary**: Update Price List Item
**Description**: Update a price list item price/configuration.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier
- `item_id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "variant_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "Updated variant UUID.",
    "default": null,
    "nested": null
  },
  "price": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "Updated unit selling price.",
    "default": null,
    "nested": null
  }
}
```

---
### `DELETE` /api/v1/price-lists/{id}/items/{item_id}
**Summary**: Delete Price List Item
**Description**: Remove a price-list item.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier
- `item_id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/pricing/resolve
**Summary**: Resolve Authoritative Price
**Description**: Resolve authoritative selling price for a product/variant in a customer context.
Never trusts frontend-supplied final unit prices.

**Request Body (JSON)**:
```json
{
  "product_id": {
    "type": "string (uuid)",
    "required": true,
    "description": "Product UUID to resolve price for.",
    "default": null,
    "nested": null
  },
  "variant_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "Optional product variant UUID.",
    "default": null,
    "nested": null
  },
  "customer_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "Optional customer UUID for tier and price list resolution.",
    "default": null,
    "nested": null
  },
  "customer_tier_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "Optional customer tier UUID override.",
    "default": null,
    "nested": null
  },
  "currency": {
    "type": "string",
    "required": false,
    "description": "Currency code for price resolution.",
    "default": "USD",
    "nested": null
  },
  "price_list_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "Optional explicit price list UUID override.",
    "default": null,
    "nested": null
  }
}
```

---

## PRODUCT-CATEGORIES (5 endpoints)

### `GET` /api/v1/product-categories
**Summary**: List Product Categories
**Description**: List product/service categories.
Used by catalog, quotation, discount-rule, and reporting screens.

**Query Parameters**:
- `is_active` (Optional[boolean], Optional): 
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `POST` /api/v1/product-categories
**Summary**: Create Product Category
**Description**: Create a product/service category.
Enforces Admin-only configuration authorization.

**Request Body (JSON)**:
```json
{
  "name": {
    "type": "string",
    "required": true,
    "description": "Category name (e.g., Hardware, Services, Subscriptions).",
    "default": null,
    "nested": null
  },
  "description": {
    "type": "Optional[string]",
    "required": false,
    "description": "Optional category description.",
    "default": null,
    "nested": null
  },
  "is_active": {
    "type": "boolean",
    "required": false,
    "description": "Whether category is active.",
    "default": true,
    "nested": null
  }
}
```

---
### `GET` /api/v1/product-categories/{id}
**Summary**: Get Product Category Details
**Description**: Return category details by UUID.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `PATCH` /api/v1/product-categories/{id}
**Summary**: Update Product Category
**Description**: Update product/service category details.
Enforces Admin-only configuration authorization.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "name": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated category name.",
    "default": null,
    "nested": null
  },
  "description": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated category description.",
    "default": null,
    "nested": null
  },
  "is_active": {
    "type": "Optional[boolean]",
    "required": false,
    "description": "Updated active status of the category.",
    "default": null,
    "nested": null
  }
}
```

---
### `DELETE` /api/v1/product-categories/{id}
**Summary**: Deactivate Product Category
**Description**: Deactivate a product category following logical-deactivation convention.
Enforces Admin-only configuration authorization.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---

## PRODUCTS (7 endpoints)

### `GET` /api/v1/products
**Summary**: List / Search Products
**Description**: List and search active or all products/services.
Supports search (by name or SKU), category filtering, and active-status filtering.
Used by quotation builder, catalog, and reporting screens.

**Query Parameters**:
- `search` (Optional[string], Optional): 
- `category_id` (Optional[string (uuid)], Optional): 
- `is_active` (Optional[boolean], Optional): 
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `POST` /api/v1/products
**Summary**: Create Product
**Description**: Create a new product or service.
Enforces Admin-only product management authorization.

**Request Body (JSON)**:
```json
{
  "category_id": {
    "type": "string (uuid)",
    "required": true,
    "description": "UUID of the product category.",
    "default": null,
    "nested": null
  },
  "name": {
    "type": "string",
    "required": true,
    "description": "Product or service name.",
    "default": null,
    "nested": null
  },
  "description": {
    "type": "Optional[string]",
    "required": false,
    "description": "Product description.",
    "default": null,
    "nested": null
  },
  "sku": {
    "type": "string",
    "required": true,
    "description": "Unique stock keeping unit identifier.",
    "default": null,
    "nested": null
  },
  "unit": {
    "type": "string",
    "required": true,
    "description": "Unit of measurement (e.g., pcs, hours, licenses).",
    "default": null,
    "nested": null
  },
  "base_price": {
    "type": "number | string",
    "required": true,
    "description": "Default selling price.",
    "default": null,
    "nested": null
  },
  "cost_price": {
    "type": "number | string",
    "required": true,
    "description": "Product cost price used for margin calculations.",
    "default": null,
    "nested": null
  },
  "tax_rate": {
    "type": "number | string",
    "required": false,
    "description": "Tax rate percentage (e.g., 18.00).",
    "default": "0.00",
    "nested": null
  },
  "is_subscription": {
    "type": "boolean",
    "required": false,
    "description": "Whether the product is recurring/subscription-based.",
    "default": false,
    "nested": null
  },
  "is_active": {
    "type": "boolean",
    "required": false,
    "description": "Whether product is active.",
    "default": true,
    "nested": null
  }
}
```

---
### `GET` /api/v1/products/{id}
**Summary**: Get Product Details
**Description**: Return complete product information required by quotation and pricing logic,
including associated category details.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `PATCH` /api/v1/products/{id}
**Summary**: Update Product
**Description**: Update product details.
Enforces Admin-only product management authorization.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "category_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "Updated product category UUID.",
    "default": null,
    "nested": null
  },
  "name": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated product name.",
    "default": null,
    "nested": null
  },
  "description": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated product description.",
    "default": null,
    "nested": null
  },
  "sku": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated SKU.",
    "default": null,
    "nested": null
  },
  "unit": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated unit of measurement.",
    "default": null,
    "nested": null
  },
  "base_price": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "Updated base selling price.",
    "default": null,
    "nested": null
  },
  "cost_price": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "Updated cost price.",
    "default": null,
    "nested": null
  },
  "tax_rate": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "Updated tax rate percentage.",
    "default": null,
    "nested": null
  },
  "is_subscription": {
    "type": "Optional[boolean]",
    "required": false,
    "description": "Updated subscription flag.",
    "default": null,
    "nested": null
  },
  "is_active": {
    "type": "Optional[boolean]",
    "required": false,
    "description": "Updated active status.",
    "default": null,
    "nested": null
  }
}
```

---
### `DELETE` /api/v1/products/{id}
**Summary**: Deactivate Product
**Description**: Deactivate a product following logical-deactivation convention.
Enforces Admin-only product management authorization.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `POST` /api/v1/products/{product_id}/variants
**Summary**: Create Product Variant
**Description**: Create a new product variant for a product.
Enforces Admin-only catalog management authorization.

**Path Parameters**:
- `product_id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "attribute_name": {
    "type": "string",
    "required": true,
    "description": "Attribute name (e.g., Size, Color, Pack).",
    "default": null,
    "nested": null
  },
  "attribute_value": {
    "type": "string",
    "required": true,
    "description": "Attribute value (e.g., Large, Red, 10-Pack).",
    "default": null,
    "nested": null
  },
  "extra_price": {
    "type": "number | string",
    "required": false,
    "description": "Price added to parent product base price.",
    "default": "0.00",
    "nested": null
  },
  "sku": {
    "type": "Optional[string]",
    "required": false,
    "description": "Optional variant-specific SKU.",
    "default": null,
    "nested": null
  },
  "is_active": {
    "type": "boolean",
    "required": false,
    "description": "Whether variant is active.",
    "default": true,
    "nested": null
  }
}
```

---
### `GET` /api/v1/products/{id}/variants
**Summary**: List Product Variants
**Description**: List variants belonging to a specific product.
Accessible to internal roles.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Query Parameters**:
- `is_active` (Optional[boolean], Optional): 
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---

## USERS (3 endpoints)

### `POST` /api/v1/users
**Summary**: Create User (Admin Only)
**Description**: Create a new application user from the administrative interface.
Requires ADMIN authorization. Supports all application roles.

**Request Body (JSON)**:
```json
{
  "name": {
    "type": "string",
    "required": true,
    "description": "Full name",
    "default": null,
    "nested": null
  },
  "email": {
    "type": "string",
    "required": true,
    "description": "Email address",
    "default": null,
    "nested": null
  },
  "password": {
    "type": "string",
    "required": true,
    "description": "Password with minimum 8 characters",
    "default": null,
    "nested": null
  },
  "role": {
    "type": "enum: ['CUSTOMER', 'SALES_REP', 'SALES_MANAGER', 'FINANCE_OPERATIONS', 'ADMIN']",
    "required": true,
    "description": "Application role assigned to user",
    "default": null,
    "nested": null
  },
  "customer_id": {
    "type": "Optional[string (uuid)]",
    "required": false,
    "description": "Optional customer account linkage",
    "default": null,
    "nested": null
  },
  "is_active": {
    "type": "boolean",
    "required": false,
    "description": "Whether the user is active",
    "default": true,
    "nested": null
  }
}
```

---
### `GET` /api/v1/users
**Summary**: List Users
**Description**: List application users. Accessible to ADMIN and SALES_MANAGER.

**Query Parameters**:
- `role` (Optional[enum: ['CUSTOMER', 'SALES_REP', 'SALES_MANAGER', 'FINANCE_OPERATIONS', 'ADMIN']], Optional): 
- `is_active` (Optional[boolean], Optional): 
- `skip` (integer, Optional): 
- `limit` (integer, Optional): 

---
### `POST` /api/v1/users/{user_id}/change-password
**Summary**: Change User Password (Admin Only)
**Description**: Administratively change the password of any user.
Requires ADMIN authorization. Revokes all active sessions of the target user.

**Path Parameters**:
- `user_id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "new_password": {
    "type": "string",
    "required": true,
    "description": "New password with minimum 8 characters",
    "default": null,
    "nested": null
  }
}
```

---

## VARIANTS (3 endpoints)

### `GET` /api/v1/variants/{id}
**Summary**: Get Variant Details
**Description**: Return product variant details by UUID.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---
### `PATCH` /api/v1/variants/{id}
**Summary**: Update Variant
**Description**: Update product variant details.
Enforces Admin-only catalog management authorization.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

**Request Body (JSON)**:
```json
{
  "attribute_name": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated attribute name.",
    "default": null,
    "nested": null
  },
  "attribute_value": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated attribute value.",
    "default": null,
    "nested": null
  },
  "extra_price": {
    "type": "Optional[number | string]",
    "required": false,
    "description": "Updated extra price.",
    "default": null,
    "nested": null
  },
  "sku": {
    "type": "Optional[string]",
    "required": false,
    "description": "Updated variant-specific SKU.",
    "default": null,
    "nested": null
  },
  "is_active": {
    "type": "Optional[boolean]",
    "required": false,
    "description": "Updated active status.",
    "default": null,
    "nested": null
  }
}
```

---
### `DELETE` /api/v1/variants/{id}
**Summary**: Deactivate Variant
**Description**: Deactivate a product variant following logical-deactivation convention.
Enforces Admin-only catalog management authorization.

**Path Parameters**:
- `id` (string (uuid)): Resource identifier

---