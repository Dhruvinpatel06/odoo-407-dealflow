# DealFlow360 Security Rule

- Authentication is implemented and owned by FastAPI.
- Store passwords only as Argon2id password hashes.
- Use short-lived access JWTs for authenticated API requests.
- Store only hashed refresh tokens in the PostgreSQL `auth_sessions` table.
- Rotate refresh tokens on refresh and revoke sessions on logout.
- Send refresh tokens through a Secure, HttpOnly cookie.
- Never log passwords, access tokens, refresh tokens, cookies, or other sensitive authentication material.
- FastAPI owns authentication, role authorization, and customer ownership checks.
- Never trust client-supplied roles or customer ownership.
- `/api/v1/portal/*` must expose only data belonging to the authenticated customer's `customer_id`.
- Disabled users must not be allowed to authenticate or use protected endpoints.
