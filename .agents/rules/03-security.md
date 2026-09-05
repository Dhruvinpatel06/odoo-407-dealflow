# DealFlow360 Security Rule

- Supabase Auth owns credentials.
- FastAPI validates Supabase-issued JWTs and owns application authorization.
- Never implement a second password/authentication system.
- Never trust frontend role checks, customer IDs, final prices, totals, approval state, inventory availability, or invoice state.
- `/api/v1/portal/*` exposes only data belonging to the authenticated customer's customer_id.
- Internal endpoints enforce role permissions server-side.
- Do not commit secrets; use environment variables.
- Do not log tokens, passwords, credentials, or sensitive authentication material.
