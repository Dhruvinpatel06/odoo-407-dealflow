# DealFlow360 Antigravity Context Pack

This package contains the project context to place into the DealFlow360 repository before implementation.

- `GEMINI.md` / `AGENTS.md`: persistent project instructions.
- `.agents/rules/`: focused workspace rules.
- `.agents/skills/`: reusable DealFlow360 skills.
- `.agents/workflows/`: repeatable implementation and verification workflows.
- `docs/IMPLEMENTATION_PLAN.md`: ordered backend execution checklist.
- `docs/specs/`: current implementation source-of-truth documents.
- `docs/specs/DealFlow360_Manual_Auth_Design.md`: authoritative manual-auth design.
- `docs/specs/DealFlow360.pdf`: original problem statement/reference; where it conflicts with the current implementation specifications, the current text specifications and manual-auth design take precedence.

Current architecture decisions:
- PostgreSQL is the application database.
- Authentication is implemented by FastAPI.
- FastAPI manual authentication is not used.
- Authentication sessions are persisted in PostgreSQL through `auth_sessions`.
- Realtime is not a core dependency.

Do not commit `.env` or secrets.
