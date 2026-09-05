# DealFlow360 — FINAL MANUAL AUTHENTICATION DESIGN

STATUS
------
Final implementation decision.

PURPOSE
-------
This document is the authoritative authentication design for DealFlow360.
It supersedes older references to FastAPI manual authentication in historical project
materials.

1. AUTHENTICATION OWNERSHIP
---------------------------
Authentication is implemented inside the FastAPI modular monolith.

FastAPI owns:
- User credential verification.
- Password hashing.
- Login.
- Access-token creation and validation.
- Refresh-token/session management.
- Logout/session revocation.
- Current-user resolution.
- Password change.
- Customer magic-link authentication if enabled by the requirements.
- Role and customer authorization.

No external authentication provider is used.

2. USER CREDENTIALS
-------------------
The `users` table is the application identity and authentication identity.

Required credential fields:
- `id`: UUID primary key.
- `name`.
- `email`: unique.
- `password_hash`: nullable only when a passwordless-only account is explicitly supported; otherwise required.
- `role`.
- `customer_id`.
- `is_active`.
- timestamps.

Rules:
- Passwords must be hashed with Argon2id.
- Never store plaintext passwords.
- Email is the login identifier.
- Client requests must never be allowed to self-assign privileged roles.
- `is_active=false` blocks authentication and protected API access.

3. ACCESS TOKENS
----------------
Use short-lived JWT access tokens.

Recommended lifetime:
- 15 minutes.

Minimum claims:
- `sub`: application `users.id`.
- `role`.
- `iat`.
- `exp`.
- unique token identifier where needed.

FastAPI validates the JWT and then resolves the application user.
Authorization is based on the current database user state, especially
`is_active`, role, and customer ownership.

4. REFRESH TOKENS AND SESSIONS
------------------------------
Use opaque, high-entropy refresh tokens rather than JWT refresh tokens.

Persist refresh-token state in:
- `auth_sessions.id`
- `auth_sessions.user_id`
- `auth_sessions.refresh_token_hash`
- `auth_sessions.expires_at`
- `auth_sessions.revoked_at`
- `auth_sessions.created_at`
- `auth_sessions.last_used_at`

Rules:
- Store only the hash of the refresh token.
- Never store the raw refresh token in PostgreSQL.
- Support multiple concurrent sessions/devices.
- Rotate the refresh token whenever `/auth/refresh` succeeds.
- Revoke the session on logout.
- Reject expired or revoked refresh tokens.

5. TOKEN TRANSPORT
------------------
Access token:
- Sent as `Authorization: Bearer <access_token>`.
- Frontend should keep the short-lived access token in memory.

Refresh token:
- Sent/stored in a Secure, HttpOnly, SameSite cookie.
- JavaScript must not directly access the refresh token.

6. CORE AUTH API
----------------
POST `/api/v1/auth/login`
- Accept email and password.
- Verify credentials and active status.
- Create an authentication session.
- Return an access token.
- Set the refresh-token cookie.

POST `/api/v1/auth/refresh`
- Read the refresh-token cookie.
- Validate the session and token hash.
- Rotate the refresh token.
- Return a new access token.

POST `/api/v1/auth/logout`
- Revoke the current authentication session.
- Clear the refresh-token cookie.

GET `/api/v1/auth/me`
- Resolve the authenticated user from the access JWT.
- Return application identity, role, active state, and customer association.

POST `/api/v1/auth/change-password`
- Require an authenticated user.
- Verify the current password.
- Store the new Argon2id hash.
- Revoke existing sessions as appropriate.

Customer magic-link endpoints may be implemented if required by the
functional requirements. They must be owned by FastAPI and must not depend
on FastAPI manual authentication.

7. AUTHORIZATION
----------------
Authentication establishes identity. Authorization remains a FastAPI
responsibility.

Request flow:
JWT -> users.id -> users.is_active/role/customer_id -> authorization
dependency -> business service.

Customer portal access must always enforce:
- authenticated CUSTOMER role;
- matching `customer_id`;
- server-side ownership checks.

8. CONFIGURATION
----------------
Authentication configuration belongs in environment-backed application
settings.

Expected settings include:
- JWT secret/key material.
- JWT algorithm.
- Access-token lifetime.
- Refresh-token lifetime.
- Cookie security settings.
- CORS/credential settings where cookie transport requires them.

Never commit secrets.

9. DEPENDENCIES
---------------
Use established Python libraries for:
- Argon2id password hashing.
- JWT encoding/decoding.
- Cryptographically secure random token generation.

Do not introduce a separate authentication service.

10. OUT OF SCOPE
----------------
Do not add:
- OAuth provider integration.
- Social login.
- A separate identity microservice.
- Redis/Kafka/Celery-based session infrastructure.
- Complex enterprise IAM functionality.

Implement only the authentication flows required by the DealFlow360 scope.
