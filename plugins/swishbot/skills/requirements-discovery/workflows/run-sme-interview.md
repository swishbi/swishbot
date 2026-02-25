# Run SME Interview

Identify subject matter experts, map process flows, and document the objects and fields that drive business logic.

## Step 1: Identify SMEs

For each source system identified during requirements discovery (CRM, POS, ERP, HRIS, etc.), find the power user — the person who knows the system inside and out.

- **One system, one SME.** Each system should have a primary point of contact. If nobody owns the system knowledge, that is a risk to flag immediately.
- **Power users over administrators.** Admins know configuration; power users know how the business actually uses the system. You want the person who builds the reports, not the person who manages user permissions.
- **Document who knows what.** Create a simple map: system → SME → their role → what they own. This becomes your interview schedule.

## Step 2: Map Process Flows

Document the end-to-end business process within each system. Every system has a "soup to nuts" flow — lead-to-close, procure-to-pay, order-to-cash, hire-to-retire.

- **Walk through the process step by step.** Ask the SME to describe what happens from the moment a record enters the system to the moment it reaches its final state.
- **Identify decision points.** Where does the process branch? What determines which path a record takes? These decision points become your business logic.
- **Capture the exceptions.** The standard flow is easy. The value is in the edge cases: "Except when the customer is in segment X, then we skip step 3 and go straight to step 5."
- **Draw the flow, not the org chart.** Focus on how data moves through the system, not who is responsible for each step.

## Step 3: Document Objects & Fields

Catalog the system objects, their fields, and relationships. Focus on the fields that drive segmentation, business rules, and KPI calculations.

- **Start with the objects the SME uses daily.** In a CRM, that might be Accounts, Opportunities, and Activities. In an ERP, Sales Orders, Invoices, and Line Items.
- **Identify the fields that matter.** Not every field is relevant. Focus on fields used for filtering, grouping, calculating, and status tracking. Ask: "When you build a report, which fields do you filter or group by?"
- **Document field combinations that encode business rules.** A single field rarely tells the whole story. "An opportunity is considered 'enterprise' when `segment = 'Enterprise'` AND `annual_revenue > 1000000` AND `employee_count > 500`" — that logic lives nowhere except the SME's head.
- **Record valid values and their meanings.** Status fields, type fields, and category fields often have values whose meaning is not obvious from the label. "Status = 'D'" might mean "Deferred" in one system and "Deleted" in another.

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*
